import requests
import re
import sqlite3

# The API endpoint for the wiki
ALL_PAGES_API = "https://fictionalcrossover.fandom.com/api.php?action=query&list=allpages&aplimit=max&format=json"

def extract_all_franchise_names():
    """Step 1: Pulls every raw page title from the wiki and saves it to a file."""
    print("Step 1: Fetching all pages from the Wiki API (this may take a moment)...")
    all_articles = []
    url = ALL_PAGES_API
    
    # Loop through pagination using the 'continue' tokens
    while url:
        response = requests.get(url)
        data = response.json()

        if 'query' in data:
            for page in data['query']['allpages']:
                all_articles.append(page['title'])
        
        if 'continue' in data:
            # Tell the API where to pick up on the next batch of 500
            url = ALL_PAGES_API + f"&apcontinue={data['continue']['apcontinue']}"
        else:
            break

    # Remove duplicates and sort alphabetically
    all_articles = sorted(list(set(all_articles)))
    
    with open('franchises_unfiltered.txt', 'w', encoding='utf-8') as file:
        for franchise in all_articles:
            file.write(franchise.strip() + "\n")
    print(f"-> Saved {len(all_articles)} raw entries to franchises_unfiltered.txt")


def filter_franchise_names():
    """Step 2: Cleans the data using Regular Expressions (Regex)."""
    print("Step 2: Filtering out promotional material, trailers, and junk metadata...")
    
    # This list defines text patterns we want to THROW AWAY
    disallowed_patterns = [
        re.compile(r".* X .*"), # Filters out crossover pages; we want base franchises first
        re.compile(r".*[c|C]ommercial"),
        re.compile(r".*[p|P]romo.*"),
        re.compile(r".*[a|A]ppearances"),
        re.compile(r".*[b|B]umper"),
        re.compile(r".*[c|C]rossover [w|W]iki.*"),
        re.compile(r".*[c|C]ameo.*"),
        re.compile(r".*[r|R]eference.*"),
        re.compile(r".*[t|T]railer.*"),
        re.compile(r".*[m|M]ascot.*"),
        re.compile(r".* [r|R]ule.*"),
    ]

    clean_franchises = []

    with open('franchises_unfiltered.txt', 'r', encoding='utf-8') as file:
        for line in file:
            franchise = line.strip()
            
            # Check if the line matches any of our junk patterns
            matches_junk = False
            for pattern in disallowed_patterns:
                if pattern.match(franchise) is not None:
                    matches_junk = True
                    break
            
            # If it's clean, keep it!
            if not matches_junk:
                clean_franchises.append(franchise)
                
    # Manually add back games that accidentally got caught by the " X " rule
    exceptions = ["Daemon X Machina", "Project X Zone"]
    for item in exceptions:
        clean_franchises.append(item)
        
    # Save the polished list
    clean_franchises = sorted(list(set(clean_franchises)))
    with open('filtered_franchises.txt', 'w', encoding='utf-8') as file:
        for franchise in clean_franchises:
            file.write(franchise + '\n')
            
    print(f"-> Filtered down to {len(clean_franchises)} clean franchises in filtered_franchises.txt")


def load_into_sqlite():
    """Step 3: Creates a SQL database and saves our clean franchises into it."""
    print("Step 3: Loading clean data into SQLite database...")
    
    # Connect to database file (creates it if it doesn't exist)
    conn = sqlite3.connect('crossovers.db')
    cursor = conn.cursor()
    
    # Create the table structure
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS franchises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)
    
    # Read our clean file and insert into SQL
    with open('filtered_franchises.txt', 'r', encoding='utf-8') as file:
        for line in file:
            franchise_name = line.strip()
            try:
                cursor.execute("INSERT INTO franchises (name) VALUES (?)", (franchise_name,))
            except sqlite3.IntegrityError:
                pass # Skip if name already exists
                
    conn.commit()
    conn.close()
    print("-> Successfully built crossovers.db and populated the 'franchises' table!")


if __name__ == "__main__":
    # Run the three steps sequentially
    extract_all_franchise_names()
    filter_franchise_names()
    load_into_sqlite()
    print("\n All tasks complete! You officially have a clean foundation data asset.")