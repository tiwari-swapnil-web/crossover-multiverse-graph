import sqlite3
import networkx as nx
import plotly.graph_objects as go

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

if __name__ == "__main__":
    search_term = input("Enter a franchise name to focus on (e.g., Street Fighter, Kingdom Hearts, Zelda): ")
    plot_ego_network(search_term, radius=1)