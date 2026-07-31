# In pipeline.py
import argparse
from src.db_manager import DatabaseManager
from src.api_fetcher import WikiAPIFetcher

# Import your original V1 modules directly from legacy/
from legacy.fetch_network import fetch_network_legacy
from legacy.step2_explore_edges import process_legacy_edges

def main():
    parser = argparse.ArgumentParser(description="Multiverse Crossover Pipeline")
    parser.add_argument("--mode", choices=["v1-seed", "v2-stream"], default="v2-stream",
                        help="Choose 'v1-seed' for legacy local file ingestion or 'v2-stream' for live API fetching")
    parser.add_argument("--target", type=str, help="Target franchise name")
    parser.add_argument("--limit", type=int, default=20, help="Batch limit")
    
    args = parser.parse_args()
    db = DatabaseManager()

    if args.mode == "v1-seed":
        print("📜 [V1 Baseline Engine] Running legacy ingestion pass...")
        fetch_network_legacy(db)
        process_legacy_edges(db)
    else:
        print("⚡ [V2 Streaming Engine] Running live API fetcher...")
        fetcher = WikiAPIFetcher(db)
        if args.target:
            fetcher.fetch_franchise_connections(args.target)
        else:
            fetcher.batch_fetch_uncached(limit=args.limit)

if __name__ == "__main__":
    main()