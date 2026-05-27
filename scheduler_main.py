import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# Bind to Railway's port immediately so the container isn't killed
class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, format, *args):
        pass

port = int(os.environ.get("PORT", 8080))
server = HTTPServer(("0.0.0.0", port), _HealthHandler)
threading.Thread(target=server.serve_forever, daemon=True).start()

print(f"[1] Health server bound to port {port}", flush=True)

print("[2] Importing pytz...", flush=True)
import pytz
print("[3] Importing APScheduler...", flush=True)
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
print("[4] Importing main...", flush=True)
from main import run_hourly, run_eod, run_alerts
print("[5] All imports OK — starting scheduler", flush=True)

ET = pytz.timezone("America/New_York")
scheduler = BlockingScheduler(
    executors={"default": ThreadPoolExecutor(1)},
    timezone=ET,
)
scheduler.add_job(run_alerts, "interval", minutes=5, id="alerts")
scheduler.add_job(run_hourly, "interval", hours=1, id="hourly")
scheduler.add_job(run_eod, "cron", day_of_week="mon-fri", hour=16, minute=30, id="eod")

print("[6] Market Agent scheduler running — alerts every 5min, hourly updates, EOD 4:30 PM ET", flush=True)
scheduler.start()
