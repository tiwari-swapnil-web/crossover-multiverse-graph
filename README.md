# 🌌 The Crossover Multiverse Graph Engine

An end-to-end network science pipeline and interactive 3D visualizer that models cross-universe crossover connections across 7,500+ media franchises into a relational, multi-dimensional graph.

---

## 📌 Features

### ⚡ V1 Core Engine (Baseline & Data Foundation)
* **ETL Ingestion:** Scrapes raw crossover listings and normalizes franchise names into relational nodes.
* **Relational SQL Database:** Stores structured nodes (`franchises`) and unique connection edges (`connections`) in SQLite.
* **Network Science & Topology:** Calculates 3D Force-Directed Spring layouts using NetworkX.
* **Community Detection:** Applies the **Louvain Algorithm** to discover organic franchise clusters (e.g., Nintendo ecosystem, Shonen Jump manga, Capcom arcade Universe).
* **Graph Centrality Metrics:** Measures Degree and Betweenness Centrality to isolate load-bearing "bridge" franchises like *Kingdom Hearts* and *MultiVersus*.

### 🚀 V2 Upgrades (Streamlit Dashboard & Live API Ingestion)
* **Live Streaming API Pipeline (`pipeline.py`):** Ingests real-time data from Fandom MediaWiki APIs using an in-memory cache layer to prevent duplicate edges and disk bloat.
* **Interactive 3D Web Dashboard (`app.py`):** Multi-tab Streamlit dashboard powered by Plotly WebGL.
* **🎯 Local Ego Network Explorer:** Extracts interactive k-hop subgraphs around any specific target franchise.
* **🛣️ Multiverse Pathfinder ("Six Degrees of Separation"):** Computes all equal-length shortest path chains between any two arbitrary franchises (e.g., *Mario* ➔ *James Bond*) and renders the combined branching network simultaneously.

---

## 🛠️ Tech Stack

* **Language:** Python 3.10+
* **Database:** SQLite
* **Network Science:** NetworkX, Community (Louvain)
* **Visualization:** Plotly (3D Dark Mode WebGL), Streamlit
* **API Integration:** Requests, MediaWiki REST API

---

## 🏗️ Architecture & Evolution

### 📜 Legacy V1 Pipeline Scripts
The project originated as a sequential, file-based batch pipeline:
* `step1_franchise_scraper.py` / `step2_clean_nodes.py`: Scrapes and builds initial SQLite nodes.
* `step3_parse_edges.py`: Parses crossover relationships into database edge tuples.
* `step4_top_hubs.py`: Queries top franchises by direct connection count.
* `step5_3d_graph.py`: Renders the baseline interactive 3D universe in Plotly.
* `step6_community_detection.py`: Runs Louvain clustering to color 3D graph communities.
* `step7_ego_network.py`: Plots a 1st-degree Ego Network for targeted franchises.
* `step8_betweenness_centrality.py`: Calculates traffic-control bridge scores across the graph.

### 🔀 V2 Modular Architecture
The V1 scripts have been modularized and extended into a dual-engine architecture:

```text
Crossover Map/
├── data/
│   └── crossovers.db          # SQLite relational database
│
├── legacy/                     # V1 Baseline Engine Scripts (step1 through step8)
│   ├── v1_ingest.py
│   ├── v1_edges.py
│   └── v1_analytics.py
│
├── src/                        # V2 Core API & Ingestion Engine
│   ├── api_fetcher.py         # Live Fandom/MediaWiki streaming API client
│   └── db_manager.py          # SQLite schema, transaction & caching logic
│
├── app.py                      # Interactive 3D Streamlit Web Dashboard
├── pipeline.py                 # CLI Execution Engine (--mode v1-seed / --mode v2-stream)
├── requirements.txt            # Python dependencies
└── README.md                   # Project documentation
```


# 📊 Key Empirical Findings
The Anchor of the Multiverse: Mario holds the highest Betweenness Centrality score (0.4477) across the connected network, sitting on roughly 45% of all shortest paths between any two disconnected franchises.

Hubs vs. Bridges: While franchises like James Bond have high raw connection counts (hubs), franchises like Kingdom Hearts and MultiVersus act as crucial structural "bridges" linking distinct media ecosystems (Disney ↔ Square Enix, Warner Bros ↔ DC/Cartoon Network).

# 🚀 Quick Start Guide
## 1. Installation & Environment Setup
```PowerShell
git clone [https://github.com/your-username/crossover-map.git](https://github.com/your-username/crossover-map.git)
cd crossover-map

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```
## 2. Ingest Data
Seed the local database using the V1 offline engine or stream live via V2:

```PowerShell
# Run V1 Seed
python pipeline.py --mode v1-seed

# Stream live API entries
python pipeline.py --mode v2-stream --limit 20
```

## 3. Launch the 3D Web Dashboard
```PowerShell
streamlit run app.py
