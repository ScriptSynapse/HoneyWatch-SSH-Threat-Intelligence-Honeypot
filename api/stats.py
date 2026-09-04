"""
Vercel serverless function: GET /api/stats

Serves a read-only sample dataset (data/demo_snapshot.json) so the HoneyWatch
dashboard has something real to call the moment it is deployed to Vercel --
no database, no VPS, no configuration required.

This is sample/demo data only. It is NOT live honeypot traffic. Vercel cannot
run the actual SSH honeypot (honeypot.py) or its always-on WebSocket server
(ws_server.py) because serverless functions cannot bind a persistent TCP
socket or keep long-lived connections open. To see real, live attack data,
run the ``backend/`` folder on a VPS (see the main README) and point the
dashboard's "Backend URL" field at it.
"""
from http.server import BaseHTTPRequestHandler
from pathlib import Path
import json

DATA_FILE = Path(__file__).parent.parent / "data" / "demo_snapshot.json"
STATS = json.loads(DATA_FILE.read_text(encoding="utf-8"))


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps(STATS).encode("utf-8")
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
