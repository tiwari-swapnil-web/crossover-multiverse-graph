import os
from bs4 import BeautifulSoup
from src.db_manager import DatabaseManager

class GraphParser:
    def __init__(self, db_manager: DatabaseManager, html_dir: str = "data/scraped_pages"):
        self.db = db_manager
        self.html_dir = html_dir

    def parse_all_cached_pages(self) -> dict:
        """Parses all HTML files in cache and updates SQLite incrementally."""
        if not os.path.exists(self.html_dir):
            return {"status": "error", "message": f"Directory '{self.html_dir}' not found."}

        new_edges = 0
        pages_processed = 0

        for filename in os.listdir(self.html_dir):
            if not filename.endswith(".html"):
                continue

            # Source franchise name derived from filename
            source_name = filename.replace(".html", "").replace("_", " ")
            source_id = self.db.upsert_franchise(source_name)

            file_path = os.path.join(self.html_dir, filename)
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                soup = BeautifulSoup(f.read(), "html.parser")

            current_type = "Type-1"

            for element in soup.find_all(['h2', 'h3', 'li', 'a']):
                text = element.get_text().strip()

                # Detect header shifts
                if "Type 1" in text or "Official Crossovers" in text:
                    current_type = "Type-1"
                    continue
                elif "Type 2" in text or "Cameos" in text or "References" in text:
                    current_type = "Type-2"
                    continue

                # Parse hyperlink targets
                if element.name == 'a' and element.get('href'):
                    target_name = text
                    
                    # Ignore standard wiki metadata links
                    if target_name and len(target_name) > 2 and not any(
                        x in target_name.lower() for x in ['edit', 'wiki', 'category', 'main page', 'special:']
                    ):
                        target_id = self.db.upsert_franchise(target_name)
                        if target_id and source_id != target_id:
                            if self.db.upsert_connection(source_id, target_id, current_type):
                                new_edges += 1

            pages_processed += 1

        nodes, edges = self.db.get_stats()
        return {
            "status": "success",
            "pages_processed": pages_processed,
            "total_nodes": nodes,
            "total_edges": edges
        }