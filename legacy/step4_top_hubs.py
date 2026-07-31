import sqlite3
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

if __name__ == "__main__":
    find_top_hubs()