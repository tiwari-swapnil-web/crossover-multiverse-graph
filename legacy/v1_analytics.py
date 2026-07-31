import sqlite3
import networkx as nx
import plotly.graph_objects as go
import plotly.express as px
import os

# Point to active V2 database path
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'crossovers.db')

def get_db_connection():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database not found at {DB_PATH}. Run pipeline.py first to build the dataset!")
    return sqlite3.connect(DB_PATH)


def find_top_hubs():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Query to count connections per franchise
    query = """
    SELECT f.name, COUNT(c.id) AS connections_count
    FROM franchises f
    JOIN connections c ON f.id = c.franchise_a_id OR f.id = c.franchise_b_id
    GROUP BY f.id
    ORDER BY connections_count DESC
    LIMIT 10;
    """

    print("🏆 Top 10 Most Connected Franchises on the Wiki:\n")
    print(f"{'Rank':<5} {'Franchise':<35} {'Connections'}")
    print("-" * 50)

    cursor.execute(query)
    for rank, (name, count) in enumerate(cursor.fetchall(), 1):
        print(f"{rank:<5} {name:<35} {count}")

    conn.close()


def generate_3d_multiverse():
    print("Connecting to database and building NetworkX graph...")
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

    # Filter out isolated nodes with zero connections for a cleaner 3D layout
    connected_nodes = [node for node, degree in G.degree() if degree > 0]
    subgraph = G.subgraph(connected_nodes)

    print(f"Loaded network: {subgraph.number_of_nodes()} connected nodes and {subgraph.number_of_edges()} edges.")
    print("Calculating 3D physics layout coordinates (Spring Layout)...")

    # 3. Calculate 3D (x, y, z) coordinates using Fruchterman-Reingold force algorithm
    pos = nx.spring_layout(subgraph, dim=3, k=0.12, iterations=40, seed=42)

    # 4. Build 3D Lines (Edges)
    edge_x, edge_y, edge_z = [], [], []
    for edge in subgraph.edges():
        x0, y0, z0 = pos[edge[0]]
        x1, y1, z1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        edge_z.extend([z0, z1, None])

    edge_trace = go.Scatter3d(
        x=edge_x, y=edge_y, z=edge_z,
        line=dict(width=1, color='#444444'),
        hoverinfo='none',
        mode='lines'
    )

    # 5. Build 3D Spheres (Nodes)
    node_x, node_y, node_z = [], [], []
    node_text, node_size, node_color = [], [], []

    for node in subgraph.nodes():
        x, y, z = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_z.append(z)
        
        name = id_to_name[node]
        degree = subgraph.degree(node)
        
        node_text.append(f"<b>{name}</b><br>Type-1 Connections: {degree}")
        # Scale node size and color based on number of connections
        node_size.append(min(3 + degree * 0.35, 22))
        node_color.append(degree)

    node_trace = go.Scatter3d(
        x=node_x, y=node_y, z=node_z,
        mode='markers',
        hoverinfo='text',
        text=node_text,
        marker=dict(
            showscale=True,
            colorscale='Plasma',
            color=node_color,
            size=node_size,
            colorbar=dict(
                thickness=15,
                title='Connections',
                xanchor='left'
            ),
            line_width=0.5
        )
    )

    print("Building interactive 3D scene...")
    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        title="3D Crossover Multiverse Map (Type-1 Connections)",
        template="plotly_dark",
        showlegend=False,
        scene=dict(
            xaxis=dict(showbackground=False, showticklabels=False, title=''),
            yaxis=dict(showbackground=False, showticklabels=False, title=''),
            zaxis=dict(showbackground=False, showticklabels=False, title='')
        ),
        margin=dict(l=0, r=0, b=0, t=40)
    )

    print("\n Launching 3D Interactive Map in your browser!")
    fig.show()

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


def plot_ego_network(target_franchise, radius=1):
    print("Connecting to database and building network...")
    conn = sqlite3.connect('crossovers.db')
    cursor = conn.cursor()

    G = nx.Graph()
    cursor.execute("SELECT id, name FROM franchises")
    id_to_name = {fid: name for fid, name in cursor.fetchall()}
    name_to_id = {name.lower(): fid for fid, name in id_to_name.items()}

    cursor.execute("SELECT franchise_a_id, franchise_b_id FROM connections")
    G.add_edges_from(cursor.fetchall())
    conn.close()

    # 1. Look up the target franchise (case-insensitive)
    target_clean = target_franchise.strip().lower()
    if target_clean not in name_to_id:
        print(f"\n❌ Could not find '{target_franchise}' in database.")
        print("Tip: Make sure the name matches how it appears on the wiki (e.g., 'Kingdom Hearts', 'Street Fighter').")
        return

    target_id = name_to_id[target_clean]
    target_exact_name = id_to_name[target_id]

    # 2. Extract Ego Subgraph (all nodes within 'radius' hops)
    ego_g = nx.ego_graph(G, target_id, radius=radius)
    print(f"\n🎯 Found Ego Network for '{target_exact_name}' (Radius = {radius}):")
    print(f"-> {ego_g.number_of_nodes()} total nodes in view ({ego_g.number_of_nodes() - 1} connected neighbors).")

    print("Calculating 3D positions for local neighborhood...")
    pos = nx.spring_layout(ego_g, dim=3, k=0.3, iterations=50, seed=42)

    # 3. Build 3D Lines
    edge_x, edge_y, edge_z = [], [], []
    for edge in ego_g.edges():
        x0, y0, z0 = pos[edge[0]]
        x1, y1, z1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        edge_z.extend([z0, z1, None])

    edge_trace = go.Scatter3d(
        x=edge_x, y=edge_y, z=edge_z,
        line=dict(width=2, color='#666666'),
        hoverinfo='none',
        mode='lines'
    )

    # 4. Build 3D Spheres (Highlight center vs neighbors)
    node_x, node_y, node_z = [], [], []
    node_text, node_size, node_color = [], [], []

    for node in ego_g.nodes():
        x, y, z = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_z.append(z)

        name = id_to_name[node]
        total_connections = G.degree(node)

        # Center node gets highlighted in glowing red/magenta
        if node == target_id:
            node_text.append(f"🎯 <b>{name} (CENTER)</b><br>Total Multiverse Connections: {total_connections}")
            node_size.append(26)
            node_color.append('#FF2D55')
        else:
            node_text.append(f"<b>{name}</b><br>Total Multiverse Connections: {total_connections}")
            node_size.append(12)
            node_color.append('#00C7FF')

    node_trace = go.Scatter3d(
        x=node_x, y=node_y, z=node_z,
        mode='markers',
        hoverinfo='text',
        text=node_text,
        marker=dict(
            color=node_color,
            size=node_size,
            line_width=0.8
        )
    )

    print("Launching 3D Local Neighborhood Map...")
    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        title=f"3D Local Neighborhood: <b>{target_exact_name}</b> (Radius = {radius})",
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

def calculate_bridge_franchises():
    print("Connecting to crossovers.db and loading network...")
    conn = sqlite3.connect('crossovers.db')
    cursor = conn.cursor()

    G = nx.Graph()

    # 1. Load nodes and edges
    cursor.execute("SELECT id, name FROM franchises")
    franchises = cursor.fetchall()
    id_to_name = {fid: name for fid, name in franchises}

    cursor.execute("SELECT franchise_a_id, franchise_b_id FROM connections")
    edges = cursor.fetchall()
    G.add_edges_from(edges)
    conn.close()

    # Filter out isolated nodes
    connected_nodes = [node for node, degree in G.degree() if degree > 0]
    subgraph = G.subgraph(connected_nodes)

    print(f"Calculating Betweenness Centrality across {subgraph.number_of_nodes()} franchises...")
    print("(This calculates which franchises act as structural bridges between distinct clusters.)\n")

    # 2. Compute Betweenness Centrality
    betweenness = nx.betweenness_centrality(subgraph)

    # 3. Sort and display Top 10 Bridges
    sorted_bridges = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:10]

    print("🌉 Top 10 Most Critical 'Bridge' Franchises in the Multiverse:")
    print("-" * 65)
    print(f"{'Rank':<5} {'Franchise':<30} {'Betweenness Score':<20} {'Connections'}")
    print("-" * 65)

    for rank, (node_id, score) in enumerate(sorted_bridges, 1):
        name = id_to_name[node_id]
        degree = subgraph.degree(node_id)
        print(f"{rank:<5} {name:<30} {score:<20.4f} {degree}")

    print("-" * 65)

if __name__ == "__main__":
    find_top_hubs()
    generate_3d_multiverse()
    generate_community_3d_graph()
    search_term = input("Enter a franchise name to focus on (e.g., Street Fighter, Kingdom Hearts, Zelda): ")
    plot_ego_network(search_term, radius=1)
    calculate_bridge_franchises()