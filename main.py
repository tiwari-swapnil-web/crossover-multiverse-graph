
import requests
import mwparserfromhell

# The base API endpoint for the Crossover Wiki
API_URL = "https://crossover.fandom.com/api.php"
SESSION = requests.Session()

def get_category_pages(category_name, limit=50):
    """Fetches a list of page titles from a specific category."""
    print(f"Fetching pages in {category_name}...")
    
    params = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": category_name,
        "cmlimit": limit,
        "format": "json"
    }

    response = SESSION.get(url=API_URL, params=params)
    data = response.json()
    
    # --- DEBUGGING PRINTS ---
    print("\n--- API Response Debug ---")
    import pprint
    pprint.pprint(data) 
    print("--------------------------\n")
    # ------------------------

    pages = []
    if "query" in data and "categorymembers" in data["query"]:
        members = data["query"]["categorymembers"]
        print(f"Found {len(members)} raw items in this category.")
        
        for item in members:
            # Filter out category/template pages (namespace 0 is standard articles)
            if item["ns"] == 0:
                pages.append(item["title"])
            else:
                print(f"Skipping non-article page: {item['title']} (Namespace: {item['ns']})")
                
    return pages

def extract_franchises_from_page(page_title):
    """Fetches the Wikitext of a page and extracts franchise names."""
    params = {
        "action": "query",
        "prop": "revisions",
        "titles": page_title,
        "rvprop": "content",
        "rvslots": "main",
        "format": "json"
    }

    response = SESSION.get(url=API_URL, params=params)
    data = response.json()
    
    pages = data.get("query", {}).get("pages", {})
    
    for page_id, page_info in pages.items():
        if "revisions" not in page_info:
            continue
            
        # Extract the raw wikitext
        wikitext = page_info["revisions"][0]["slots"]["main"]["*"]
        
        # Parse the wikitext
        parsed_text = mwparserfromhell.parse(wikitext)
        
        # Look for templates (Infoboxes) in the page
        for template in parsed_text.filter_templates():
            # Check if this is the standard crossover infobox
            if "Infobox Crossover" in template.name or "Infobox" in template.name:
                
                # These parameter names ("franchise1", "series_a") vary by wiki.
                # You will need to adjust these based on how the Crossover Wiki formats them!
                if template.has("franchise1") and template.has("franchise2"):
                    f1 = str(template.get("franchise1").value).strip()
                    f2 = str(template.get("franchise2").value).strip()
                    return (f1, f2)
                    
    return None

# --- Main Execution ---
if __name__ == "__main__":
    # 1. Use ONLY the actual category name (no browser title text or pipes)
    target_category = "Category:Type_1_links"  
    test_pages = get_category_pages(target_category, limit=5)
    
    # 2. Extract data from those pages
    for title in test_pages:
        print(f"\nAnalyzing page: {title}")
        connections = extract_franchises_from_page(title)
        
        if connections:
            print(f" -> Found Connection: {connections[0]} <---> {connections[1]}")
        else:
            print(" -> Could not extract standard infobox data.")

