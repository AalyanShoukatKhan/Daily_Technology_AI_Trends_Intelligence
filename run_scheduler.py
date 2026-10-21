"""Separate scheduler process. Run only one instance."""
import logging
from app import app
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from services.pipeline import run_pipeline
from services.digest_builder import build_digest
from services.notifications.email_sender import send_email
from zoneinfo import ZoneInfo
logging.basicConfig(level=logging.INFO)
def collect():
    with app.app_context():
        logging.info("Scheduled pipeline: %s",run_pipeline())
def digest():
    with app.app_context():
        result=build_digest()
        if app.config["EMAIL_ENABLED"]:
            send_email(result["subject"],result["text"],result["html"])
        logging.info("Digest created: %s items",result["item_count"])
if __name__=="__main__":
    zone=ZoneInfo(app.config["TIME_ZONE"])
    scheduler=BlockingScheduler(timezone=zone)
    scheduler.add_job(collect,"interval",hours=app.config["COLLECTION_INTERVAL_HOURS"],id="collect",max_instances=1,coalesce=True)
    scheduler.add_job(digest,CronTrigger(hour=app.config["DIGEST_HOUR"],minute=0,timezone=zone),id="digest",max_instances=1,coalesce=True)
    logging.info("Scheduler started in %s. Keep this process separate from Flask.",app.config["TIME_ZONE"])
    scheduler.start()
