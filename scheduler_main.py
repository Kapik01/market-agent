import logging
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytz
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.executors.pool import ThreadPoolExecutor

from main import run_hourly, run_eod, run_alerts

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

ET = pytz.timezone("America/New_York")


class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        pass  # suppress HTTP access logs


def _start_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), _HealthHandler)
    server.serve_forever()


# Railway requires a process to bind a port — run health server in background
threading.Thread(target=_start_health_server, daemon=True).start()

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
