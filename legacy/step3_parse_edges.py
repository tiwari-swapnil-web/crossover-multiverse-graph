import sqlite3

def build_network_edges():
    print("Connecting to crossovers.db...")
    conn = sqlite3.connect('crossovers.db')
    cursor = conn.cursor()

    # 1. Create the connections table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS connections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            franchise_a_id INTEGER NOT NULL,
            franchise_b_id INTEGER NOT NULL,
            FOREIGN KEY(franchise_a_id) REFERENCES franchises(id),
            FOREIGN KEY(franchise_b_id) REFERENCES franchises(id),
            CONSTRAINT unique_pair UNIQUE (franchise_a_id, franchise_b_id)
        )
    """)

    # 2. Build a fast lookup dictionary { "Mario": 102, "Zelda": 105, ... }
    cursor.execute("SELECT name, id FROM franchises")
    name_to_id = {name: fid for name, fid in cursor.fetchall()}
    print(f"Loaded {len(name_to_id)} franchise lookup keys from SQL.")

    # 3. Read the unfiltered text file and process all " X " lines
    print("Parsing crossover relationships...")
    with open('franchises_unfiltered.txt', 'r', encoding='utf-8') as file:
        lines = file.readlines()

    inserted_count = 0
    skipped_count = 0

    for line in lines:
        line = line.strip()
        if " X " in line:
            # Split the line at the " X " delimiter
            parts = line.split(" X ")
            if len(parts) == 2:
                name_a, name_b = parts[0].strip(), parts[1].strip()

                # Verify both franchises exist in our clean database
                if name_a in name_to_id and name_b in name_to_id:
                    id_a = name_to_id[name_a]
                    id_b = name_to_id[name_b]

                    # Ensure id_a < id_b to prevent duplicate reverse edges
                    if id_a > id_b:
                        id_a, id_b = id_b, id_a

                    try:
                        cursor.execute(
                            "INSERT INTO connections (franchise_a_id, franchise_b_id) VALUES (?, ?)",
                            (id_a, id_b)
                        )
                        inserted_count += 1
                    except sqlite3.IntegrityError:
                        # Skip if connection is already recorded
                        skipped_count += 1

    conn.commit()
    conn.close()

    print(f"\n Success! Saved {inserted_count} unique crossover edges to crossovers.db.")
    if skipped_count > 0:
        print(f"-> Skipped {skipped_count} duplicate connections.")

if __name__ == "__main__":
    build_network_edges()