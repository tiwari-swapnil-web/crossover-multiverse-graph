import sqlite3
import networkx as nx
import plotly.graph_objects as go
import plotly.express as px

def generate_community_3d_graph():
    print("Connecting to crossovers.db and loading network...")
    conn = sqlite3.connect('crossovers.db')
    cursor = conn.cursor()

    G = nx.Graph()

    # 1. Load franchises as nodes
    cursor.execute("SELECT id, name FROM franchises")
    franchises = cursor.fetchall()
    id_to_name = {fid: name for fid, name in franchises}
    for fid, name in franchises:
        G.add_node(fid, name=name)

    # 2. Load connections as edges
    cursor.execute("SELECT franchise_a_id, franchise_b_id FROM connections")
    edges = cursor.fetchall()
    G.add_edges_from(edges)
    conn.close()

    # Filter out isolated nodes
    connected_nodes = [node for node, degree in G.degree() if degree > 0]
    subgraph = G.subgraph(connected_nodes)

    print(f"Loaded {subgraph.number_of_nodes()} connected franchises.")
    print("Running Louvain Community Detection algorithm...")

    # 3. Detect Communities / Clusters using Louvain algorithm
    communities = list(nx.community.louvain_communities(subgraph, seed=42))
    print(f"-> Discovered {len(communities)} distinct community clusters in the multiverse!")

    # Map each node ID to its assigned Community Group ID
    node_to_community = {}
    for comm_id, community_set in enumerate(communities):
        for node_id in community_set:
            node_to_community[node_id] = comm_id

    # Print out the Top 5 largest clusters to the terminal
    print("\n Top 5 Largest Multiverse Clusters Discovered:")
    print("-" * 55)
    sorted_communities = sorted(communities, key=len, reverse=True)
    for rank, comm_set in enumerate(sorted_communities[:5], 1):
        # Find the highest degree nodes in this specific cluster
        sub_g = subgraph.subgraph(comm_set)
        top_members = sorted(sub_g.degree(), key=lambda x: x[1], reverse=True)[:4]
        top_names = [id_to_name[nid] for nid, _ in top_members]
        print(f"Cluster {rank} ({len(comm_set)} franchises): e.g., {', '.join(top_names)}")
    print("-" * 55)

    print("\nCalculating 3D positions...")
    pos = nx.spring_layout(subgraph, dim=3, k=0.12, iterations=40, seed=42)

    # 4. Prepare Plotly 3D Data
    edge_x, edge_y, edge_z = [], [], []
    for edge in subgraph.edges():
        x0, y0, z0 = pos[edge[0]]
        x1, y1, z1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        edge_z.extend([z0, z1, None])

    edge_trace = go.Scatter3d(
        x=edge_x, y=edge_y, z=edge_z,
        line=dict(width=1, color='#333333'),
        hoverinfo='none',
        mode='lines'
    )

    node_x, node_y, node_z = [], [], []
    node_text, node_size, node_color = [], [], []

    # Palette of distinct colors for the clusters
    color_palette = px.colors.qualitative.Dark24

    for node in subgraph.nodes():
        x, y, z = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_z.append(z)
        
        name = id_to_name[node]
        degree = subgraph.degree(node)
        comm_id = node_to_community[node]
        
        node_text.append(f"<b>{name}</b><br>Cluster ID: #{comm_id}<br>Connections: {degree}")
        node_size.append(min(4 + degree * 0.35, 24))
        # Assign a color from our palette based on community ID
        node_color.append(color_palette[comm_id % len(color_palette)])

    node_trace = go.Scatter3d(
        x=node_x, y=node_y, z=node_z,
        mode='markers',
        hoverinfo='text',
        text=node_text,
        marker=dict(
            color=node_color,
            size=node_size,
            line_width=0.5
        )
    )

    print("Launching updated 3D Cluster Visualizer...")
    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        title="3D Crossover Multiverse — Community Clusters (Louvain Algorithm)",
        template="plotly_dark",
        showlegend=False,
        scene=dict(
            xaxis=dict(showbackground=False, showticklabels=False, title=''),
            yaxis=dict(showbackground=False, showticklabels=False, title=''),
            zaxis=dict(showbackground=False, showticklabels=False, title='')
        ),
        margin=dict(l=0, r=0, b=0, t=40)
    )

    fig.show()

if __name__ == "__main__":
    generate_community_3d_graph()