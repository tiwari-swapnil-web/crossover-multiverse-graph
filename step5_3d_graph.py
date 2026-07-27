import sqlite3
import networkx as nx
import plotly.graph_objects as go

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

if __name__ == "__main__":
    generate_3d_multiverse()