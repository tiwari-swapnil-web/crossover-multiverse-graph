import argparse
from src.db_manager import DatabaseManager
from src.api_fetcher import WikiAPIFetcher

def main():
    parser = argparse.ArgumentParser(description="Multiverse Cartographer Pipeline CLI")
    parser.add_argument(
        "--mode", 
        choices=["fetch-api", "stats"], 
        default="fetch-api",
        help="Pipeline mode"
    )
    parser.add_argument("--limit", type=int, default=20, help="Max franchises to query per run")
    parser.add_argument("--target", type=str, help="Specific target franchise (e.g., --target 'Arknights')")

    args = parser.parse_args()
    db = DatabaseManager()
    fetcher = WikiAPIFetcher(db_manager=db)

    if args.target:
        print(f"🌐 In-memory API query for target: '{args.target}'...")
        count = fetcher.fetch_franchise_connections(args.target)
        print(f"✅ Extracted {count} connections for '{args.target}' directly into database!")

    if args.mode == "fetch-api":
        results = fetcher.batch_fetch_uncached(limit=args.limit)
        print(f"\n✅ Batch complete! Processed {results['processed']} pages, mapped {results['new_edges']} new connections.")

    nodes, edges = db.get_stats()
    print("\n🌌 --- Multiverse Database Metrics ---")
    print(f" Total Franchises (Nodes): {nodes}")
    print(f" Total Connections (Edges): {edges}")

if __name__ == "__main__":
    main()