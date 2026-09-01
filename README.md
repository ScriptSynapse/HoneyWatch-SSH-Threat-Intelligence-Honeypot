# 🍯 HoneyWatch — SSH Honeypot + Threat Intelligence Platform

A dashboard for an SSH honeypot: stateful shell emulation, GeoIP enrichment,
attack-pattern detection, malware capture, a real-time WebSocket feed, and a
world-map view of attacker origins.

## Read this first: what Vercel can and can't run here

**Vercel cannot host the actual honeypot.** `honeypot.py` opens a real TCP
socket and waits for SSH connections 24/7; `ws_server.py` keeps a persistent
WebSocket open to push live events. Both need a process that stays running
indefinitely on a fixed port. Vercel only runs short-lived serverless
functions that start on a request and shut down after — there's no way to
`bind()` a long-lived listener there, for SSH or for WebSockets.

So this repo is split in two, and that split is the fix:

| Folder | What it is | Where it runs |
|---|---|---|
| **`index.html`** + **`api/`** | The dashboard UI, plus two small serverless functions that hand it a realistic sample dataset | **Vercel** |
| **`backend/`** | The real SSH honeypot, the SQLite database, the WebSocket/API server, alerting, PDF reports | **A VPS or any always-on machine you control** |

Deploy `index.html`/`api/` to Vercel and you get a fully working, publicly
reachable dashboard the moment it builds — no server, no database, no signup,
browsing sample attack data out of the box. If you also want it to show your
own honeypot's live traffic, run `backend/` on a VPS (instructions below) and
point the dashboard at it. That part was always going to need a real server;
no amount of Vercel configuration changes that.

*(This also explains a real bug in the original dashboard: its JavaScript only
ever tried to reach `http://localhost:PORT` for its API and WebSocket calls.
Deployed anywhere other than your own laptop, that always fails silently and
the dashboard falls back to sample data — permanently. That's fixed here: the
dashboard now resolves, in order, a backend URL you configure → a local
`ws_server.py` on `localhost` for development → this deployment's own `/api/*`
sample-data functions → and only then the fully offline embedded fallback.)*

---

## 1. Deploy the dashboard to Vercel

```bash
npm i -g vercel        # if you don't have it
vercel                 # from the repo root; accept the defaults
```

Or connect the GitHub repo at [vercel.com/new](https://vercel.com/new) — no
build command, no output directory, no environment variables required. Vercel
will serve `index.html` as the site and `api/stats.py` / `api/alerts.py` as
Python serverless functions automatically because they live in `api/`.

Log in with **anything** (any username/password) and you'll see the sample
dataset. Use `admin` / `honeywatch` specifically to force the fully offline,
no-network demo mode instead.

## 2. (Optional) Run the real honeypot and point the dashboard at it

This is the part that needs a real, always-on server — a $5–6/mo VPS
(DigitalOcean, Linode, Hetzner, etc.) works fine.

```bash
# On your VPS
git clone <this-repo-url> honeywatch && cd honeywatch/backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

python seed_logs.py     # optional: pre-populate 14 days of demo data
python ws_server.py     # starts the API + WebSocket server (prints its port)

# in a second terminal/session
python honeypot.py      # the actual SSH honeypot, listens on port 2222 by default
```

Put a TLS reverse proxy (Caddy, nginx + certbot) in front of `ws_server.py`'s
port so it's reachable at `https://your-domain`. This matters: your Vercel
dashboard is served over HTTPS, and browsers block a HTTPS page from calling
a plain `http://` API (mixed content). A one-line Caddyfile is enough:

```
your-domain.example.com {
    reverse_proxy localhost:8080
}
```

Then, on the Vercel-hosted dashboard's login screen, put
`https://your-domain.example.com` in the **Backend URL** field and log in
with the real credentials (default `admin` / `honeywatch` — **change this
immediately**, see below). The dashboard will now show your honeypot's actual
traffic, polling `/api/stats` every 30s and upgrading to a live WebSocket feed
automatically. The Backend URL is remembered in your browser (`localStorage`)
so you only enter it once.

For running the honeypot itself continuously, use the provided systemd unit
(adjust paths/user first):

```ini
# /etc/systemd/system/honeywatch.service
[Unit]
Description=HoneyWatch SSH Honeypot
After=network.target

[Service]
Type=simple
User=honeypot
WorkingDirectory=/opt/honeywatch/backend
ExecStart=/opt/honeywatch/backend/venv/bin/python honeypot.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now honeywatch
```

Run `ws_server.py` the same way as a second unit (or under `screen`/`tmux`
while you're testing).

### Security — do this before exposing it publicly

- **Change the default login immediately**: `python auth.py passwd admin <new-password>` (12+ chars). The default is `admin` / `honeywatch`, printed as a warning in the logs on first run — treat that warning as a checklist item, not a feature.
- **Set a stable `HONEYWATCH_SECRET` env var** before starting `ws_server.py`. Without it, a new random JWT signing key is generated every restart, which silently logs everyone out.
- **Never run the honeypot on a machine with real data, credentials, or other services on it.** Use a dedicated, isolated VPS.
- Restrict outbound traffic on the honeypot host to just what you need (see the firewall snippet in `backend/`'s inline docs / original design) so a compromised fake shell can't be used to pivot anywhere.

---

## Local development

Run the backend and dashboard together exactly as before — `backend/` is a
complete, self-contained copy of the original project:

```bash
cd backend
pip install -r requirements.txt
python seed_logs.py
python ws_server.py     # serves the dashboard itself at http://localhost:<port>
# in another terminal:
python honeypot.py
```

Open the URL `ws_server.py` prints (NOT `dashboard.html` directly as a
`file://` URL — browsers block its API calls under `file://`). The Windows
launchers (`setup_and_run_v2.bat` / `.ps1`) still work unchanged from inside
`backend/`.

---

## Project layout

```
.
├── index.html            # dashboard — deployed as the Vercel site
├── api/
│   ├── stats.py          # GET /api/stats  — sample data, Vercel serverless function
│   └── alerts.py         # GET /api/alerts — sample data, Vercel serverless function
├── data/
│   ├── demo_snapshot.json  # the sample dataset served by api/stats.py
│   └── demo_alerts.json    # the sample alerts served by api/alerts.py
├── vercel.json
├── backend/               # run this on your own VPS — NOT deployed to Vercel
│   ├── honeypot.py         # SSH server — fake shell, tarpit, malware capture
│   ├── fake_fs.py          # stateful virtual filesystem + canary credentials
│   ├── threat_intel.py     # GeoIP, AbuseIPDB, attack-pattern detection, alerting
│   ├── database.py         # SQLite backend
│   ├── auth.py             # login, JWT sessions, password hashing
│   ├── alerts.py           # spike monitor + email/Discord/Slack notifications
│   ├── report_gen.py       # PDF report generation
│   ├── ws_server.py        # aiohttp API + WebSocket server
│   ├── seed_logs.py        # generates 14 days of realistic demo data
│   ├── dashboard.html      # same dashboard as index.html, for local dev via ws_server.py
│   ├── requirements.txt
│   ├── setup_and_run_v2.ps1
│   └── setup_and_run_v2.bat
└── README.md
```

---

## Features

- **SQLite database** (`backend/logs/honeypot.db`) — `sessions`, `auth_attempts`, `commands`, `suspicious_events`, `malware_captures`, `ip_reputation`, fully indexed.
- **GeoIP enrichment** via ip-api.com — country, city, ISP, ASN, lat/lon, cached 24h.
- **AbuseIPDB integration** (optional, needs a free API key) — abuse confidence score, Tor exit-node detection.
- **Kaspersky OpenTIP integration** (optional, needs a free API key from [opentip.kaspersky.com/token](https://opentip.kaspersky.com/token)) — Red/Orange/Yellow/Grey/Green threat zone per IP, combined with AbuseIPDB's score (highest wins) into the same risk score used everywhere else in the dashboard.
- **Attack pattern detection** — classifies each auth attempt as `dictionary_attack`, `targeted_bruteforce`, `credential_stuffing`, `botnet_sweep`, or generic `bruteforce`.
- **Canary/deception credentials** planted in the fake filesystem (`/root/.aws/credentials`, `/root/.ssh/id_rsa`, `/root/.env`, `/var/www/html/wp-config.php`, etc.) to see what attackers go after.
- **Tarpit delays** (0.5–2.0s per auth attempt) to waste brute-force tool time.
- **Real malware capture** — if an attacker's `wget`/`curl` points at a real URL, the honeypot fetches and hashes the payload.
- **Live WebSocket feed** when connected to a real `ws_server.py` backend; polling fallback otherwise.
- **Six dashboard pages**: Overview, World Map, Credentials, Activity, Threats, Malware.

### Configuring the backend

Threat-intel API keys are read from environment variables (recommended, keeps
secrets out of git) with the old in-file constants as a fallback:

```bash
export ABUSEIPDB_KEY="your_abuseipdb_key"           # https://www.abuseipdb.com/api — free tier: 1000/day
export KASPERSKY_OPENTIP_KEY="your_opentip_key"      # https://opentip.kaspersky.com/token — free
```

Both are optional and independent — set either, both, or neither. When both
are set, `threat_intel.py` takes the *higher* of the two risk scores for each
IP (an IP flagged `Red` by Kaspersky but unlisted on AbuseIPDB is still
treated as high-risk, and vice versa), so this is additive coverage rather
than a replacement. The combined score drives the same `abuse_score` column
that already feeds the dashboard's IP table colors, the world map, alert
thresholds, and PDF reports — no other changes needed to see it show up.

If you'd rather hardcode a key for local testing, `threat_intel.py` still
has `ABUSEIPDB_KEY` / `KASPERSKY_KEY` constants at the top — just don't
commit real keys to git if you do.

```python
# backend/threat_intel.py
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/..."
```

```python
# backend/honeypot.py
PORT = 22   # production; requires root or authbind — see below
```

```bash
# Run on port 22 without root (Linux)
sudo apt install authbind
sudo touch /etc/authbind/byport/22
sudo chmod 500 /etc/authbind/byport/22
sudo chown $USER /etc/authbind/byport/22
authbind --deep python honeypot.py
```

### Useful queries against the SQLite log

```sql
-- Every credential attempt
SELECT timestamp, peer_ip, username, password, result, attack_type
FROM auth_attempts ORDER BY timestamp DESC LIMIT 100;

-- Attackers by country
SELECT r.country, COUNT(DISTINCT a.peer_ip) AS ips, COUNT(*) AS attempts
FROM auth_attempts a JOIN ip_reputation r ON a.peer_ip = r.ip
GROUP BY r.country ORDER BY attempts DESC;

-- Critical suspicious events
SELECT timestamp, peer_ip, suspicious_type, detail
FROM suspicious_events WHERE severity = 'critical'
ORDER BY timestamp DESC;
```

---

## Legal notice

Deploy the honeypot only on infrastructure you own or are explicitly
authorized to use for security research. Collecting honeypot traffic is
generally legitimate, but you're responsible for complying with local laws on
network monitoring and data retention.
