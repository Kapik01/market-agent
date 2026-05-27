import logging
import sys
import pytz
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.executors.pool import ThreadPoolExecutor

from main import run_hourly, run_eod, run_alerts

# Log to stdout so Railway captures it in their log viewer
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

ET = pytz.timezone("America/New_York")

scheduler = BlockingScheduler(
    executors={"default": ThreadPoolExecutor(1)},
    timezone=ET,
)

scheduler.add_job(run_alerts, "interval", minutes=5, id="alerts")
scheduler.add_job(run_hourly, "interval", hours=1, id="hourly")
scheduler.add_job(run_eod, "cron", day_of_week="mon-fri", hour=16, minute=30, id="eod")

if __name__ == "__main__":
    logging.info("Market Agent scheduler starting — alerts every 5min, hourly updates, EOD at 4:30 PM ET")
    scheduler.start()
