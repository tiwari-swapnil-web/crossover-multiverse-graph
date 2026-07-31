import os
import time
import urllib.parse
import urllib.request
from src.db_manager import DatabaseManager

class WikiScraper:
    def __init__(self, db_manager: DatabaseManager, cache_dir: str = "data/scraped_pages"):
        self.db = db_manager
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        # Browser-like User-Agent to avoid standard Fandom bot throttling
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) MultiverseCartographerBot/2.0'
        }

    def sanitize_filename(self, name: str) -> str:
        return "".join([c if c.isalnum() or c in (' ', '_', '-') else '_' for c in name]).strip()

    def fetch_page(self, franchise_name: str) -> str:
        """
        Fetches wiki page HTML for a given franchise.
        Returns: 'downloaded', 'cached', or 'failed'
        """
        clean_name = self.sanitize_filename(franchise_name)
        filepath = os.path.join(self.cache_dir, f"{clean_name}.html")

        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            return "cached"

        encoded_title = urllib.parse.quote(franchise_name.replace(" ", "_"))
        # Fandom Crossover Wiki correct subdomain
        url = f"https://fictionalcrossover.fandom.com/wiki/{encoded_title}"

        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req) as response:
                if response.status == 200:
                    html_content = response.read().decode('utf-8', errors='ignore')
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(html_content)
                    time.sleep(0.3)  # Polite 300ms delay
                    return "downloaded"
        except Exception:
            return "failed"
        return "failed"

    def fetch_uncached_franchises(self, limit: int = 50) -> int:
        """Fetches wiki pages for franchises currently in database that aren't cached yet."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM franchises ORDER BY id ASC")
            all_franchises = [row[0] for row in cursor.fetchall()]

        downloaded = 0
        print(f"🌐 Scraping wiki pages for uncached franchises (Batch limit: {limit})...")
        
        for name in all_franchises:
            if downloaded >= limit:
                break
            clean_name = self.sanitize_filename(name)
            filepath = os.path.join(self.cache_dir, f"{clean_name}.html")
            
            if not os.path.exists(filepath):
                status = self.fetch_page(name)
                if status == "downloaded":
                    downloaded += 1
                    print(f"  ↳ Saved: {name}")

        return downloaded