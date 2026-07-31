import html
import json
import re
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

class WikiAPIFetcher:
    def __init__(self, db_manager):
        self.db = db_manager
        self.api_url = "https://fictionalcrossover.fandom.com/api.php"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*'
        }

    def clean_title(self, title: str) -> str:
        """Sanitizes raw/legacy titles for MediaWiki API lookups."""
        if not title:
            return ""

        # 1. Decode HTML entities (&amp; -> &, &#39; -> ', &quot; -> ")
        t = html.unescape(title)

        # 2. Normalize Unicode (NFC) & collapse irregular whitespace (\xa0, tabs, double spaces)
        t = unicodedata.normalize('NFC', t)
        t = re.sub(r'\s+', ' ', t).strip()

        # 3. Strip matched outer wrapper double quotes ("Title" -> Title)
        if len(t) >= 2 and t.startswith('"') and t.endswith('"'):
            t = t[1:-1].strip()

        # 4. Strip matched outer single quotes ONLY if both ends match ('Title' -> Title)
        # Preserves leading apostrophes like 'Salem's Lot
        if len(t) >= 2 and t.startswith("'") and t.endswith("'"):
            t = t[1:-1].strip()

        return t

    def get_candidate_titles(self, raw_title: str) -> list:
        """Generates an ordered list of title variations to attempt against MediaWiki API."""
        cleaned = self.clean_title(raw_title)
        candidates = []

        if cleaned:
            candidates.append(cleaned)

            # Candidate 2: Try adding leading apostrophe if missing (e.g., 'Salem's Lot)
            if not cleaned.startswith("'"):
                candidates.append(f"'{cleaned}")

            # Candidate 3: Swap Ampersand formats (" & " <-> " and ")
            if " & " in cleaned:
                candidates.append(cleaned.replace(" & ", " and "))
            elif " and " in cleaned:
                candidates.append(cleaned.replace(" and ", " & "))

        # Candidate 4: Unmodified raw input as last resort
        if raw_title and raw_title not in candidates:
            candidates.append(raw_title)

        return candidates

    def _query_api(self, franchise_name: str) -> int:
        """Internal helper to execute MediaWiki parse API request."""
        params = {
            'action': 'parse',
            'page': franchise_name,
            'prop': 'links',
            'redirects': '1',  # Automatically follow redirects
            'format': 'json'
        }
        url = f"{self.api_url}?{urllib.parse.urlencode(params)}"

        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode('utf-8', errors='ignore'))
                
                if 'error' in data:
                    return 0

                parse_data = data.get('parse', {})
                links = parse_data.get('links', [])
                if not links:
                    return 0

                canonical_title = parse_data.get('title', franchise_name)
                source_id = self.db.upsert_franchise(canonical_title)
                
                added_count = 0
                for link in links:
                    # ns == 0 means Main Article namespace
                    if link.get('ns') != 0:
                        continue
                        
                    target_title = link.get('*', '').strip()
                    if not target_title:
                        continue

                    target_id = self.db.upsert_franchise(target_title)
                    self.db.upsert_connection(source_id, target_id)
                    added_count += 1
                
                return added_count
        except Exception:
            return 0

    def fetch_franchise_connections(self, raw_franchise_name: str) -> int:
        candidates = self.get_candidate_titles(raw_franchise_name)
        
        for candidate in candidates:
            count = self._query_api(candidate)
            if count > 0:
                return count

        print(f"    ⚠️ Wiki notice for '{raw_franchise_name}': Page not found across all candidates.")
        return 0

    def batch_fetch_uncached(self, limit: int = 20) -> dict:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM franchises ORDER BY id ASC LIMIT ?", (limit,))
            franchises = [row[0] for row in cursor.fetchall()]

        total_connections = 0
        processed = 0

        print(f"⚡ [In-Memory API Fetch] Batch processing up to {len(franchises)} franchises...")
        for name in franchises:
            count = self.fetch_franchise_connections(name)
            processed += 1
            total_connections += count
            print(f"  ↳ '{name}' -> Found {count} connections")
            time.sleep(0.3)

        return {"processed": processed, "new_edges": total_connections}