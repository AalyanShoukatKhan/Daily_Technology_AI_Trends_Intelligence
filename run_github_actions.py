"""One-shot pipeline for scheduled GitHub Actions runs."""
import logging
import os

from app import app
from services.pipeline import run_pipeline
from services.digest_builder import build_digest
from services.notifications.email_sender import send_email

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

def main() -> int:
    if os.getenv("EMAIL_ENABLED", "false").lower() != "true":
        logging.error("EMAIL_ENABLED must be true for the scheduled workflow.")
        return 1

    with app.app_context():
        # Importing app initializes the SQLite schema and seeds default feed sources.
        pipeline_result = run_pipeline()
        logging.info("Collection result: %s", pipeline_result)
        if pipeline_result.get("feeds_succeeded", 0) == 0:
            logging.error("No feed sources succeeded; refusing to send a misleading digest.")
            return 1

        digest = build_digest()
        logging.info("Built digest with %s stories.", digest["item_count"])
        outcome = send_email(digest["subject"], digest["text"], digest["html"])
        if not outcome.get("ok"):
            logging.error("Email delivery failed: %s", outcome.get("message", "unknown error"))
            return 1
        logging.info("Digest email submitted successfully to the configured recipient.")
        return 0

if __name__ == "__main__":
    raise SystemExit(main())
