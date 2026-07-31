import sqlite3

def init_db():
    conn = sqlite3.connect("crossover_network.db")
    cursor = conn.cursor()

    # Table 1: Nodes (The individual franchises/universes)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS nodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            url TEXT
        )
    ''')

    # Table 2: Edges (The structural connections between two nodes)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS edges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_node TEXT NOT NULL,
            target_node TEXT NOT NULL,
            source_page_title TEXT NOT NULL,
            FOREIGN KEY(source_node) REFERENCES nodes(name),
            FOREIGN KEY(target_node) REFERENCES nodes(name),
            UNIQUE(source_node, target_node) ON CONFLICT IGNORE
        )
    ''')

    conn.commit()
    conn.close()
    print("Database initialized successfully with Node/Edge schema!")

if __name__ == "__main__":
    init_db()