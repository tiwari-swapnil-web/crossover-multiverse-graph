import streamlit as st
import sqlite3
import os
import networkx as nx
import plotly.graph_objects as go
import plotly.express as px

# -----------------------------------------------------------------------------
# 1. Page Configuration & Custom Dark Styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Multiverse Crossover Map Engine",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark glassmorphic styling
st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    .stMetric { background-color: #161B22; padding: 15px; border-radius: 10px; border: 1px solid #30363D; }
    div[data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #30363D; }
    </style>
""", unsafe_allow_html=True)

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'crossovers.db')

# -----------------------------------------------------------------------------
# 2. Cached Data Ingestion & Graph Building
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600)
def load_graph_data():
    """Loads nodes and edges from crossovers.db into a NetworkX Graph."""
    if not os.path.exists(DB_PATH):
        return None, {}, {}

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id, name FROM franchises")
    franchises = cursor.fetchall()
    id_to_name = {fid: name for fid, name in franchises}
    name_to_id = {name.lower(): fid for fid, name in id_to_name.items()}

    G = nx.Graph()
    for fid, name in franchises:
        G.add_node(fid, name=name)

    # Use franchise_a_id and franchise_b_id to match crossovers.db
    cursor.execute("SELECT franchise_a_id, franchise_b_id FROM connections")
    edges = cursor.fetchall()
    G.add_edges_from(edges)
    conn.close()

    # Subgraph of connected nodes (excluding isolated nodes)
    connected_nodes = [node for node, degree in G.degree() if degree > 0]
    subgraph = G.subgraph(connected_nodes).copy()

    return subgraph, id_to_name, name_to_id

# -----------------------------------------------------------------------------
# 3. Sidebar KPI Metrics & Global Navigation
# -----------------------------------------------------------------------------
subgraph, id_to_name, name_to_id = load_graph_data()

st.sidebar.title("🌌 Multiverse Engine")
st.sidebar.caption("Interactive 3D Network Analytics & Discovery")

if subgraph is None:
    st.error("❌ Database `data/crossovers.db` not found. Please run `py pipeline.py` first!")
    st.stop()

# Sidebar KPI Cards
st.sidebar.subheader("📊 Live Network Stats")
col_s1, col_s2 = st.sidebar.columns(2)
col_s1.metric("Nodes", f"{subgraph.number_of_nodes():,}")
col_s2.metric("Edges", f"{subgraph.number_of_edges():,}")

navigation = st.sidebar.radio(
    "Select Dashboard Mode:",
    ["🌌 3D Multiverse Clusters", "🎯 Ego Explorer", "📈 Structural Centrality", "🛣️ Multiverse Pathfinder"]
)

# -----------------------------------------------------------------------------
# MODE 1: 3D Multiverse Clusters (Louvain Community Detection)
# -----------------------------------------------------------------------------
if navigation == "🌌 3D Multiverse Clusters":
    st.title("🌌 3D Multiverse Cluster Map")
    st.write("Interactive 3D topology showing natural franchise clusters detected via the Louvain Community Algorithm.")

    col_ctrl1, col_ctrl2 = st.columns([1, 3])
    with col_ctrl1:
        color_mode = st.selectbox("Color Nodes By:", ["Community Clusters", "Degree (Connections)"])
        max_nodes = st.slider("Render Limit (Top Connected Nodes):", min_value=100, max_value=subgraph.number_of_nodes(), value=400, step=50)

    # Filter top nodes for smooth rendering
    top_nodes = sorted(subgraph.degree(), key=lambda x: x[1], reverse=True)[:max_nodes]
    active_ids = [node for node, _ in top_nodes]
    active_subgraph = subgraph.subgraph(active_ids)

    # Compute Louvain & 3D layout
    communities = list(nx.community.louvain_communities(active_subgraph, seed=42))
    node_to_comm = {nid: cid for cid, comm in enumerate(communities) for nid in comm}
    pos = nx.spring_layout(active_subgraph, dim=3, k=0.15, iterations=35, seed=42)

    # Build Plotly 3D Edges
    edge_x, edge_y, edge_z = [], [], []
    for edge in active_subgraph.edges():
        x0, y0, z0 = pos[edge[0]]
        x1, y1, z1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        edge_z.extend([z0, z1, None])

    edge_trace = go.Scatter3d(
        x=edge_x, y=edge_y, z=edge_z,
        line=dict(width=1, color='#333333'),
        hoverinfo='none', mode='lines'
    )

    # Build Plotly 3D Nodes
    node_x, node_y, node_z, node_text, node_size, node_color = [], [], [], [], [], []
    palette = px.colors.qualitative.Dark24

    for node in active_subgraph.nodes():
        x, y, z = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_z.append(z)
        
        name = id_to_name[node]
        degree = active_subgraph.degree(node)
        comm_id = node_to_comm.get(node, 0)

        node_text.append(f"<b>{name}</b><br>Connections: {degree}<br>Cluster ID: #{comm_id}")
        node_size.append(min(4 + degree * 0.3, 20))
        
        if color_mode == "Community Clusters":
            node_color.append(palette[comm_id % len(palette)])
        else:
            node_color.append(degree)

    node_trace = go.Scatter3d(
        x=node_x, y=node_y, z=node_z,
        mode='markers', hoverinfo='text', text=node_text,
        marker=dict(
            color=node_color,
            colorscale='Plasma' if color_mode != "Community Clusters" else None,
            size=node_size,
            line_width=0.5
        )
    )

    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        template="plotly_dark",
        scene=dict(
            xaxis=dict(showbackground=False, showticklabels=False, title=''),
            yaxis=dict(showbackground=False, showticklabels=False, title=''),
            zaxis=dict(showbackground=False, showticklabels=False, title='')
        ),
        margin=dict(l=0, r=0, b=0, t=20),
        height=700
    )

    st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------------------------------
# MODE 2: Target Ego Explorer (Local Neighborhood)
# -----------------------------------------------------------------------------
elif navigation == "🎯 Ego Explorer":
    st.title("🎯 Local Ego Network Explorer")
    st.write("Inspect the immediate crossover neighborhood around any specific target franchise.")

    col1, col2 = st.columns([2, 1])
    with col1:
        # Search dropdown with popular defaults
        default_options = ["Mario", "Zelda", "Street Fighter", "Kingdom Hearts", "James Bond", "Donkey Kong"]
        selected_name = st.selectbox("Search or Select Target Franchise:", default_options + sorted(list(id_to_name.values())))
    with col2:
        radius = st.slider("Neighborhood Radius (Hops):", min_value=1, max_value=2, value=1)

    target_id = name_to_id.get(selected_name.lower())

    if target_id is None or target_id not in subgraph:
        st.warning(f"Franchise '{selected_name}' was not found in active connections.")
    else:
        ego_g = nx.ego_graph(subgraph, target_id, radius=radius)
        pos = nx.spring_layout(ego_g, dim=3, k=0.25, iterations=40, seed=42)

        # Build Edges
        edge_x, edge_y, edge_z = [], [], []
        for edge in ego_g.edges():
            x0, y0, z0 = pos[edge[0]]
            x1, y1, z1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            edge_z.extend([z0, z1, None])

        edge_trace = go.Scatter3d(
            x=edge_x, y=edge_y, z=edge_z,
            line=dict(width=2, color='#555555'),
            hoverinfo='none', mode='lines'
        )

        # Build Nodes
        node_x, node_y, node_z, node_text, node_size, node_color = [], [], [], [], [], []

        for node in ego_g.nodes():
            x, y, z = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_z.append(z)

            name = id_to_name[node]
            connections = subgraph.degree(node)

            if node == target_id:
                node_text.append(f"🎯 <b>{name} (CENTER)</b><br>Total Connections: {connections}")
                node_size.append(24)
                node_color.append('#FF2D55')  # Magenta/Red
            else:
                node_text.append(f"<b>{name}</b><br>Total Connections: {connections}")
                node_size.append(12)
                node_color.append('#00C7FF')  # Bright Cyan

        node_trace = go.Scatter3d(
            x=node_x, y=node_y, z=node_z,
            mode='markers', hoverinfo='text', text=node_text,
            marker=dict(color=node_color, size=node_size, line_width=0.8)
        )

        fig = go.Figure(data=[edge_trace, node_trace])
        fig.update_layout(
            title=f"Local Neighborhood for <b>{id_to_name[target_id]}</b> ({len(ego_g.nodes())-1} direct neighbors)",
            template="plotly_dark",
            scene=dict(
                xaxis=dict(showbackground=False, showticklabels=False, title=''),
                yaxis=dict(showbackground=False, showticklabels=False, title=''),
                zaxis=dict(showbackground=False, showticklabels=False, title='')
            ),
            margin=dict(l=0, r=0, b=0, t=40),
            height=650
        )

        st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------------------------------
# MODE 3: Network Centrality & Bridge Analytics
# -----------------------------------------------------------------------------
elif navigation == "📈 Structural Centrality":
    st.title("📈 Multiverse Structural Analytics")
    st.write("Evaluating structural importance using Degree and Betweenness Centrality.")

    tab1, tab2 = st.tabs(["🏆 Degree Centrality (Top Hubs)", "🌉 Betweenness Centrality (Bridge Franchises)"])

    with tab1:
        st.subheader("Top Most Connected Franchises")
        degree_sorted = sorted(subgraph.degree(), key=lambda x: x[1], reverse=True)[:15]
        
        table_data = []
        for rank, (nid, count) in enumerate(degree_sorted, 1):
            table_data.append({"Rank": rank, "Franchise": id_to_name[nid], "Direct Connections": count})
        
        st.table(table_data)

    with tab2:
        st.subheader("Top 'Bridge' Franchises (Betweenness Centrality)")
        st.caption("Measures how often a franchise sits on the shortest path between any two disconnected clusters.")
        
        # Calculate Betweenness on cached subgraph (top 300 for speed)
        top_nodes = [n for n, _ in sorted(subgraph.degree(), key=lambda x: x[1], reverse=True)[:300]]
        sub_g = subgraph.subgraph(top_nodes)
        betweenness = nx.betweenness_centrality(sub_g)
        sorted_bridges = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:15]

        bridge_data = []
        for rank, (nid, score) in enumerate(sorted_bridges, 1):
            bridge_data.append({
                "Rank": rank,
                "Franchise": id_to_name[nid],
                "Betweenness Score": f"{score:.4f}",
                "Connections": subgraph.degree(nid)
            })

        st.table(bridge_data)

# -----------------------------------------------------------------------------
# MODE 4: Multiverse Pathfinder ("Six Degrees of Separation")
# -----------------------------------------------------------------------------
elif navigation == "🛣️ Multiverse Pathfinder":
    st.title("🛣️ Multiverse Crossover Pathfinder")
    st.write("Find all equal-length shortest crossover paths between any two arbitrary franchises.")

    sorted_franchises = sorted(list(id_to_name.values()))
    
    col1, col2 = st.columns(2)
    with col1:
        start_default = sorted_franchises.index("Mario") if "Mario" in sorted_franchises else 0
        start_name = st.selectbox("Start Franchise:", sorted_franchises, index=start_default)
    with col2:
        target_default = sorted_franchises.index("James Bond") if "James Bond" in sorted_franchises else 1
        target_name = st.selectbox("Target Franchise:", sorted_franchises, index=target_default)

    start_id = name_to_id.get(start_name.lower())
    target_id = name_to_id.get(target_name.lower())

    if start_id is None or target_id is None or start_id not in subgraph or target_id not in subgraph:
        st.warning("One or both selected franchises are not present in the active network graph.")
    elif start_id == target_id:
        st.info("Start and Target franchises are identical!")
    else:
        try:
            # 🟢 Fetch ALL equal-length shortest paths
            all_paths = list(nx.all_shortest_paths(subgraph, source=start_id, target=target_id))
            num_paths = len(all_paths)
            degrees = len(all_paths[0]) - 1

            if num_paths > 1:
                st.info(f"🔀 Found **{num_paths} alternate shortest routes** with **{degrees} degrees of separation**!")
            else:
                st.success(f"🎯 **Unique Shortest Connection Found! ({degrees} degree{'s' if degrees > 1 else ''} of separation)**")

            # 1. Print all route chains line-by-line
            st.markdown("### 🔗 Crossover Chains")
            for i, path in enumerate(all_paths, 1):
                route_str = " ➔ ".join([f"**`{id_to_name[nid]}`**" for nid in path])
                st.markdown(f"**Route #{i}:** {route_str}")

            # 2. Combine all unique nodes and edges across all routes for 3D plot
            all_path_nodes = list(set(nid for path in all_paths for nid in path))
            
            path_edges = set()
            for path in all_paths:
                for i in range(len(path) - 1):
                    u, v = path[i], path[i+1]
                    if u > v:
                        u, v = v, u
                    path_edges.add((u, v))

            path_subgraph = subgraph.subgraph(all_path_nodes)
            pos = nx.spring_layout(path_subgraph, dim=3, k=0.35, seed=42)

            # Build 3D Edges
            edge_x, edge_y, edge_z = [], [], []
            for u, v in path_edges:
                x0, y0, z0 = pos[u]
                x1, y1, z1 = pos[v]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])
                edge_z.extend([z0, z1, None])

            edge_trace = go.Scatter3d(
                x=edge_x, y=edge_y, z=edge_z,
                line=dict(width=4, color='#00C7FF'),
                hoverinfo='none', mode='lines'
            )

            # Build 3D Nodes
            node_x, node_y, node_z, node_text, node_size, node_color = [], [], [], [], [], []
            for nid in all_path_nodes:
                x, y, z = pos[nid]
                node_x.append(x)
                node_y.append(y)
                node_z.append(z)

                name = id_to_name[nid]
                if nid == start_id:
                    role = "START FRANCHISE"
                    color = '#34C759'  # Bright Green
                    size = 22
                elif nid == target_id:
                    role = "TARGET FRANCHISE"
                    color = '#FF2D55'  # Bright Magenta/Red
                    size = 22
                else:
                    role = "BRIDGE STEP"
                    color = '#FFCC00'  # Gold
                    size = 16

                node_text.append(f"<b>{name}</b><br>Role: {role}")
                node_size.append(size)
                node_color.append(color)

            node_trace = go.Scatter3d(
                x=node_x, y=node_y, z=node_z,
                mode='markers+text', hoverinfo='text',
                text=[id_to_name[nid] for nid in all_path_nodes],
                textposition="top center",
                marker=dict(color=node_color, size=node_size, line_width=1)
            )

            fig = go.Figure(data=[edge_trace, node_trace])
            fig.update_layout(
                template="plotly_dark",
                scene=dict(
                    xaxis=dict(showbackground=False, showticklabels=False, title=''),
                    yaxis=dict(showbackground=False, showticklabels=False, title=''),
                    zaxis=dict(showbackground=False, showticklabels=False, title='')
                ),
                margin=dict(l=0, r=0, b=0, t=20),
                height=550
            )
            st.plotly_chart(fig, use_container_width=True)

        except nx.NetworkXNoPath:
            st.error(f"❌ No crossover path exists between **{start_name}** and **{target_name}** in the current database.")