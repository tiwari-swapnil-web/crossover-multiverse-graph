# 🕸️ The Crossover Multiverse Graph (V1 Engine)

A graph analysis pipeline that scrapes, parses, models, and visualizes cross-universe connections across 800+ media franchises into a relational 3D network.

## 📌 Features (V1 Core Engine)
- **ETL Pipeline:** Scrapes raw crossover listings and normalizes franchise names.
- **Relational SQL Database:** Stores clean nodes (`franchises`) and unique structural edges (`connections`) in SQLite.
- **Network Science & Physics:** Calculates 3D Force-Directed Spring layouts using NetworkX.
- **Community Detection:** Runs the Louvain Algorithm to detect organic franchise clusters.
- **Graph Metrics:** Computes Degree Centrality and Betweenness Centrality to isolate "bridge" franchises like *Kingdom Hearts* and *MultiVersus*.
- **Ego Networks:** Isolates focal neighborhoods for targeted visual analysis.

## 🛠️ Tech Stack
- **Language:** Python 3
- **Database:** SQLite
- **Network Science:** NetworkX
- **Visualization:** Plotly (3D Dark Mode WebGL)

## 🚀 Script Overview
- `step1_franchise_scraper.py` / `step2_clean_nodes.py`: Scrapes and builds SQLite nodes.
- `step3_parse_edges.py`: Parses crossover relationships into database edges.
- `step4_top_hubs.py`: Queries Top 10 franchises by connection count.
- `step5_3d_graph.py`: Renders the baseline interactive 3D universe.
- `step6_community_detection.py`: Runs Louvain clustering and colors 3D galaxies.
- `step7_ego_network.py`: Plots a 1st-degree Ego Network for any targeted franchise.
- `step8_betweenness_centrality.py`: Calculates traffic-control bridge scores.

---
*V2 Streamlit Dashboard coming soon!*