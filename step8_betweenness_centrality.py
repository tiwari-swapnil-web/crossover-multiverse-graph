import sqlite3
import networkx as nx

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
    calculate_bridge_franchises()