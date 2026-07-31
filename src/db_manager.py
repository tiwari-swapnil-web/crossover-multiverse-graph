import sqlite3
from typing import Tuple, Optional

class DatabaseManager:
    def __init__(self, db_path: str = "data/crossovers.db"):
        self.db_path = db_path
        self._auto_migrate()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _auto_migrate(self):
        """Automatically checks and upgrades schema to support V2 features."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Ensure core tables exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS franchises (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS connections (
                    franchise_a_id INTEGER NOT NULL,
                    franchise_b_id INTEGER NOT NULL,
                    PRIMARY KEY (franchise_a_id, franchise_b_id),
                    FOREIGN KEY (franchise_a_id) REFERENCES franchises(id),
                    FOREIGN KEY (franchise_b_id) REFERENCES franchises(id)
                )
            """)

            # 2. Add connection_type column if missing
            cursor.execute("PRAGMA table_info(connections)")
            cols = [col[1] for col in cursor.fetchall()]
            if 'connection_type' not in cols:
                cursor.execute("ALTER TABLE connections ADD COLUMN connection_type TEXT DEFAULT 'Type-1'")

            conn.commit()

    def upsert_franchise(self, name: str) -> Optional[int]:
        """Gets franchise ID or creates a new entry if it doesn't exist (Leaf Node support)."""
        clean_name = name.strip()
        if not clean_name:
            return None

        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Try to get existing ID
            cursor.execute("SELECT id FROM franchises WHERE LOWER(name) = LOWER(?)", (clean_name,))
            row = cursor.fetchone()
            if row:
                return row[0]
            
            # Otherwise insert as new leaf node
            try:
                cursor.execute("INSERT INTO franchises (name) VALUES (?)", (clean_name,))
                conn.commit()
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                cursor.execute("SELECT id FROM franchises WHERE LOWER(name) = LOWER(?)", (clean_name,))
                return cursor.fetchone()[0]

    def upsert_connection(self, franchise_a_id: int, franchise_b_id: int, conn_type: str = "Type-1") -> bool:
        """Inserts a connection without throwing errors on duplicates."""
        if franchise_a_id == franchise_b_id:
            return False

        u, v = min(franchise_a_id, franchise_b_id), max(franchise_a_id, franchise_b_id)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO connections (franchise_a_id, franchise_b_id, connection_type)
                VALUES (?, ?, ?)
                ON CONFLICT(franchise_a_id, franchise_b_id) DO UPDATE SET
                connection_type = excluded.connection_type
            """, (u, v, conn_type))
            conn.commit()
            return cursor.rowcount > 0

    def get_stats(self) -> Tuple[int, int]:
        """Returns total counts of franchises and edges."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            nodes = cursor.execute("SELECT COUNT(*) FROM franchises").fetchone()[0]
            edges = cursor.execute("SELECT COUNT(*) FROM connections").fetchone()[0]
            return nodes, edges