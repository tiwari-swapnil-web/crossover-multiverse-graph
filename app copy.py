import sqlite3
import networkx as nx
import plotly.graph_objects as go
import streamlit as st

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Multiverse Cartographer",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- LOAD DATA & NETWORK ---
@st.cache_data
def load_network_data():
    conn = sqlite3.connect('data/crossovers.db')
    cursor = conn.cursor()

    cursor.execute("SELECT id, name FROM franchises")
    id_to_name = {fid: name for fid, name in cursor.fetchall()}
    name_to_id = {name.lower(): fid for fid, name in id_to_name.items()}

    G = nx.Graph()
    # Safely add all nodes so state lookups never fail
    G.add_nodes_from(id_to_name.keys())

    cursor.execute("SELECT franchise_a_id, franchise_b_id FROM connections")
    edges = cursor.fetchall()
    valid_edges = [(a, b) for a, b in edges if a in id_to_name and b in id_to_name]
    G.add_edges_from(valid_edges)
    conn.close()

    # Assign Universal Stream IDs
    stream_ids = {}
    for fid, name in id_to_name.items():
        degree = G.degree(fid) if G.has_node(fid) else 0
        clean_code = "".join([c for c in name if c.isalnum()]).upper()[:4] or "NODE"
        stream_ids[fid] = f"STREAM-{clean_code}-{degree:03d}"

    return G, id_to_name, name_to_id, stream_ids

G, id_to_name, name_to_id, stream_ids = load_network_data()

# Calculate 3D layout ONLY for connected nodes (keeps math lightning fast!)
@st.cache_data
def get_3d_positions(_graph):
    active_nodes = [node for node, deg in _graph.degree() if deg > 0]
    subgraph = _graph.subgraph(active_nodes)
    return nx.spring_layout(subgraph, dim=3, k=0.3, iterations=30, seed=42)

pos = get_3d_positions(G)

# --- SIDEBAR UI ---
st.sidebar.title("🌌 Multiverse Cartographer")
st.sidebar.markdown("*Navigation & Multiverse Analytics Engine*")
st.sidebar.divider()

mode = st.sidebar.radio("Select Navigation Mode:", ["🛸 Explorer View", "🎯 Pathfinder (Shortest Path)"])

all_franchises = sorted(list(id_to_name.values()))

default_index = 0
for idx, name in enumerate(all_franchises):
    if name.lower() == "mario":
        default_index = idx
        break

# --- MODE 1: EXPLORER VIEW ---
if mode == "🛸 Explorer View":
    st.sidebar.subheader("Node Inspector")
    selected_name = st.sidebar.selectbox("Target Franchise:", all_franchises, index=default_index)
    
    target_id = name_to_id[selected_name.lower()]
    target_neighbors = set(G.neighbors(target_id)) if G.has_node(target_id) else set()
    neighbors_names = [id_to_name[nbr] for nbr in target_neighbors if nbr in id_to_name]
    
    st.sidebar.info(f"**Universal Stream ID:** `{stream_ids.get(target_id, 'STREAM-UNK-000')}`")
    st.sidebar.metric("Direct Crossover Connections", len(neighbors_names))
    
    with st.sidebar.expander("Connected Franchises"):
        if neighbors_names:
            st.write(", ".join(sorted(neighbors_names)))
        else:
            st.write("No direct crossover connections found in database.")

    # Build 3D Plotly Visualization
    edge_x, edge_y, edge_z = [], [], []
    for edge in G.edges():
        if edge[0] in pos and edge[1] in pos:
            x0, y0, z0 = pos[edge[0]]
            x1, y1, z1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            edge_z.extend([z0, z1, None])

    edge_trace = go.Scatter3d(x=edge_x, y=edge_y, z=edge_z, line=dict(width=1, color='#333344'), hoverinfo='none', mode='lines')

    node_x, node_y, node_z, node_text, node_color, node_size = [], [], [], [], [], []
    for node in pos: # Only iterate over active positioned nodes
        x, y, z = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_z.append(z)
        
        name = id_to_name.get(node, f"Franchise #{node}")
        sid = stream_ids.get(node, "UNKNOWN")
        deg = G.degree(node)
        
        node_text.append(f"<b>{name}</b><br>ID: {sid}<br>Connections: {deg}")
        
        if node == target_id:
            node_color.append('#FF0055') # Target node
            node_size.append(18)
        elif node in target_neighbors:
            node_color.append('#00E5FF') # 1st degree neighbor
            node_size.append(10)
        else:
            node_color.append('#444466') # Background
            node_size.append(4)

    node_trace = go.Scatter3d(
        x=node_x, y=node_y, z=node_z, mode='markers', hoverinfo='text',
        text=node_text, marker=dict(color=node_color, size=node_size, line_width=0.5)
    )

    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        template="plotly_dark", title=f"Focused Sector: {selected_name} ({stream_ids.get(target_id, '')})",
        scene=dict(xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False)),
        margin=dict(l=0, r=0, b=0, t=40), height=700
    )
    # Change this:
    # st.plotly_chart(fig, use_container_width=True)

    # To this:
    st.plotly_chart(fig, width="stretch")

# --- MODE 2: PATHFINDER (SHORTEST PATH) ---
elif mode == "🎯 Pathfinder (Shortest Path)":
    st.sidebar.subheader("Route Configuration")
    start_franchise = st.sidebar.selectbox("Start Point (Franchise A):", all_franchises, index=0)
    end_franchise = st.sidebar.selectbox("Destination (Franchise B):", all_franchises, index=min(10, len(all_franchises)-1))
    
    start_id = name_to_id[start_franchise.lower()]
    end_id = name_to_id[end_franchise.lower()]

    if G.has_node(start_id) and G.has_node(end_id) and nx.has_path(G, start_id, end_id):
        path = nx.shortest_path(G, start_id, end_id)
        path_names = [id_to_name[nid] for nid in path if nid in id_to_name]
        
        st.success(f"**Path Found!** Connected in **{len(path) - 1} hops**:")
        st.markdown(" ➡️ ".join([f"`{name}`" for name in path_names]))
        
        path_edges = set(zip(path[:-1], path[1:]))
        
        bg_edge_x, bg_edge_y, bg_edge_z = [], [], []
        for edge in G.edges():
            if edge not in path_edges and (edge[1], edge[0]) not in path_edges:
                if edge[0] in pos and edge[1] in pos:
                    x0, y0, z0 = pos[edge[0]]
                    x1, y1, z1 = pos[edge[1]]
                    bg_edge_x.extend([x0, x1, None])
                    bg_edge_y.extend([y0, y1, None])
                    bg_edge_z.extend([z0, z1, None])

        bg_edge_trace = go.Scatter3d(x=bg_edge_x, y=bg_edge_y, z=bg_edge_z, line=dict(width=0.8, color='#222233'), hoverinfo='none', mode='lines')

        path_edge_x, path_edge_y, path_edge_z = [], [], []
        for u, v in path_edges:
            if u in pos and v in pos:
                x0, y0, z0 = pos[u]
                x1, y1, z1 = pos[v]
                path_edge_x.extend([x0, x1, None])
                path_edge_y.extend([y0, y1, None])
                path_edge_z.extend([z0, z1, None])

        path_edge_trace = go.Scatter3d(x=path_edge_x, y=path_edge_y, z=path_edge_z, line=dict(width=6, color='#FFD700'), hoverinfo='none', mode='lines')

        path_set = set(path)
        node_x, node_y, node_z, node_text, node_color, node_size = [], [], [], [], [], []
        for node in pos:
            x, y, z = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_z.append(z)
            name = id_to_name.get(node, f"Franchise #{node}")
            
            if node in path_set:
                node_text.append(f"🌟 <b>{name} (PATH STEP)</b>")
                node_color.append('#FFD700')
                node_size.append(16)
            else:
                node_text.append(name)
                node_color.append('#222233')
                node_size.append(3)

        node_trace = go.Scatter3d(x=node_x, y=node_y, z=node_z, mode='markers', hoverinfo='text', text=node_text, marker=dict(color=node_color, size=node_size))

        fig = go.Figure(data=[bg_edge_trace, path_edge_trace, node_trace])
        fig.update_layout(
            template="plotly_dark", title=f"Multiverse Path: {start_franchise} ➡️ {end_franchise}",
            scene=dict(xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False)),
            margin=dict(l=0, r=0, b=0, t=40), height=700
        )
        # Change this:
        # st.plotly_chart(fig, use_container_width=True)
    
        # To this:
        st.plotly_chart(fig, width="stretch")
    else:
        st.error("No crossover path exists between these two franchises (or one of them is completely isolated).")