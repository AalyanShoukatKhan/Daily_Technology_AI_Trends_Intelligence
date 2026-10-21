import argparse
from app import app
from services.pipeline import run_pipeline
from services.feed_fetcher import test_feed
from database import get_db
def main():
    parser=argparse.ArgumentParser(description="Technology intelligence pipeline")
    parser.add_argument("--once",action="store_true",help="Run one collection cycle")
    parser.add_argument("--dry-run",action="store_true",help="Fetch enabled feeds and report entries without storing articles")
    parser.add_argument("--source-test",help="Test a configured feed by source name")
    args=parser.parse_args()
    with app.app_context():
        if args.source_test:
            source=get_db().execute("SELECT * FROM feed_sources WHERE name=?",(args.source_test,)).fetchone()
            if not source: print("Source not found"); raise SystemExit(1)
            print(test_feed(source["feed_url"])); return
        if args.dry_run:
            from services.feed_fetcher import fetch_feed
            sources=get_db().execute("SELECT * FROM feed_sources WHERE enabled=1").fetchall()
            for source in sources:
                try: print(f"{source['name']}: {len(fetch_feed(source['feed_url']))} entries")
                except Exception as exc: print(f"{source['name']}: ERROR {exc}")
            return
        print(run_pipeline())
if __name__=="__main__": main()
