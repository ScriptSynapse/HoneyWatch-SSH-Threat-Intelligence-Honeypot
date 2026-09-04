"""
Vercel serverless function: GET /api/alerts

Serves a read-only sample alert feed (data/demo_alerts.json) to match
dashboard.html's expected shape ({"alerts": [...]}). Sample data only -- see
api/stats.py and the main README for why this can't be live data on Vercel.
"""
from http.server import BaseHTTPRequestHandler
from pathlib import Path
import json

DATA_FILE = Path(__file__).parent.parent / "data" / "demo_alerts.json"
ALERTS = json.loads(DATA_FILE.read_text(encoding="utf-8"))


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps(ALERTS).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "public, max-age=60")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
