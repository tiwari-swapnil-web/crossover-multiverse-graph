import argparse
from src.db_manager import DatabaseManager
from src.api_fetcher import WikiAPIFetcher

# Cleanly import V1 legacy modules from legacy/
try:
    from legacy.v1_ingest import run_v1_ingestion
    from legacy.v1_edges import run_v1_edge_builder
    V1_AVAILABLE = True
except ImportError:
    V1_AVAILABLE = False

def main():
    parser = argparse.ArgumentParser(description="Multiverse Crossover Map Engine")
    parser.add_argument("--mode", choices=["v1-seed", "v2-stream"], default="v2-stream",
                        help="Choose 'v1-seed' for offline text/regex seeding or 'v2-stream' for live API streaming")
    parser.add_argument("--target", type=str, help="Target franchise name for V2 API stream")
    parser.add_argument("--limit", type=int, default=20, help="Batch limit for V2 processing")

    args = parser.parse_args()
    db = DatabaseManager()

    if args.mode == "v1-seed":
        if not V1_AVAILABLE:
            print("❌ V1 scripts not found in legacy/. Please ensure legacy/v1_ingest.py and legacy/v1_edges.py exist.")
            return
        
        print("\n🏛️ --- Executing V1 Baseline Data Pipeline ---")
        run_v1_ingestion()
        run_v1_edge_builder()
    
    else:
        print("\n⚡ --- Executing V2 Streaming API Pipeline ---")
        fetcher = WikiAPIFetcher(db)
        if args.target:
            fetcher.fetch_franchise_connections(args.target)
        else:
            fetcher.batch_fetch_uncached(limit=args.limit)

    # Print Database Metrics
    nodes, edges = db.get_stats()
    print("\n🌌 --- Multiverse Database Metrics ---")
    print(f" Total Franchises (Nodes): {nodes}")
    print(f" Total Connections (Edges): {edges}")

if __name__ == "__main__":
    main()