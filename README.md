# 🍯 HoneyWatch — SSH Honeypot & Threat Intelligence Platform

HoneyWatch is a fake SSH server that logs everything an attacker does to it,
enriches every connection with GeoIP and abuse-reputation data, and shows the
result on a live dashboard: a world map of attacker origins, credential and
command feeds, malware captures, and downloadable PDF reports.

It ships in two parts, deployed to two different places:

| Part | What it does | Runs on |
|---|---|---|
| **Dashboard** (`index.html`, `api/`) | The UI, plus two tiny serverless functions that hand it a sample dataset so it works with zero setup | **Vercel** (or any static host) |
| **Backend** (`backend/`) | The real SSH honeypot, SQLite database, WebSocket/API server, alerting, PDF reports | **A VPS or any machine you leave running** |

That split isn't optional — it's a consequence of what each side can do.
Vercel runs short-lived serverless functions that start on a request and exit
right after; there's no way for it to keep a TCP socket open for incoming SSH
connections or hold a WebSocket open for a live feed. A real honeypot needs a
process that's still listening at 3 a.m. when someone tries `root`/`admin`
against it, so that part has to live on a server you control.

---

## Quick start — dashboard only (2 minutes, no server)

```bash
npm i -g vercel        # if you don't have it
vercel                 # from the repo root, accept the defaults
```

Or connect the repo at [vercel.com/new](https://vercel.com/new) — no build
command, no output directory, no environment variables needed. Vercel serves
`index.html` as the site and turns `api/stats.py` / `api/alerts.py` into
Python serverless functions automatically because they live under `api/`.

Log in with **anything** — the login form only gates access to the demo UI
here, it isn't checking a real password — and you'll see a realistic sample
dataset: ~8,600 login attempts, 15 attacker IPs across 10 countries, a
malware download feed, and a full world map. This is fixed sample data (see
`data/demo_snapshot.json`), not live traffic; there is no honeypot running
behind a bare Vercel deploy.

## Full setup — real honeypot feeding the dashboard

This is the part that needs an always-on box — a $5–6/mo VPS (DigitalOcean,
Linode, Hetzner, etc.) is plenty.

```bash
# On your VPS
git clone https://github.com/ScriptSynapse/HoneyWatch-SSH-Threat-Intelligence-Honeypot.git
cd HoneyWatch-SSH-Threat-Intelligence-Honeypot/backend

python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

python seed_logs.py     # optional: pre-populate ~14 days of realistic demo data
python ws_server.py     # API + WebSocket server — prints the port it picked

# in a second terminal
python honeypot.py      # the actual SSH honeypot, listens on port 2222 by default
```

`ws_server.py` also serves the dashboard itself, so open the URL it prints
(e.g. `http://localhost:8080`) rather than opening `dashboard.html` directly
as a `file://` path — browsers block the API/WebSocket calls under `file://`.
Default login is `admin` / `honeywatch`; the server logs a warning about this
on first run, and you should change it before exposing anything publicly
(see [Security](#security-checklist) below).

### Pointing the Vercel dashboard at your real honeypot

Put a TLS reverse proxy in front of `ws_server.py` so it's reachable over
HTTPS — the Vercel dashboard is served over HTTPS, and browsers block an
HTTPS page from calling a plain `http://` API. A minimal Caddyfile:

```
your-domain.example.com {
    reverse_proxy localhost:8080
}
```

Then, on the Vercel dashboard's login screen, enter
`https://your-domain.example.com` in the **Backend URL** field and log in
with your real credentials. The dashboard now polls `/api/stats` every 30s
and upgrades to a live WebSocket feed automatically. The Backend URL is
remembered in your browser so you only enter it once.

### Keeping it running

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

Set up a second unit the same way for `ws_server.py` (or run it under
`screen`/`tmux` while testing). On Windows, `setup_and_run_v2.bat` /
`setup_and_run_v2.ps1` in `backend/` handle dependency install, database
seeding, and launching `ws_server.py` in one step.

### Security checklist

Before this touches the public internet:

- **Change the default login**: `python auth.py passwd admin <new-password>`
  (12+ characters). `admin` / `honeywatch` is printed as a warning in the
  logs on first run — treat that as a to-do, not a feature.
- **Set a stable `HONEYWATCH_SECRET` environment variable** before starting
  `ws_server.py`. Without it, a new random JWT signing key is generated on
  every restart, which silently logs everyone out and invalidates every
  existing session.
- **Never run the honeypot on a machine with real data, credentials, or
  other services on it.** Use a dedicated, isolated VPS — assume anything
  the fake shell can see, an attacker can eventually get to.
- **Restrict outbound traffic** on the honeypot host to what it actually
  needs. `honeypot.py` will genuinely fetch and hash URLs an attacker feeds
  it via `wget`/`curl` (that's how malware capture works) — don't let that
  same box pivot anywhere you care about.

---

## Project layout

```
.
├── index.html              # dashboard — deployed as the Vercel site
├── api/
│   ├── stats.py             # GET /api/stats  — serves data/demo_snapshot.json
│   └── alerts.py            # GET /api/alerts — serves data/demo_alerts.json
├── data/
│   ├── demo_snapshot.json   # sample dataset behind api/stats.py
│   └── demo_alerts.json     # sample alerts behind api/alerts.py
├── vercel.json
├── backend/                 # run this on your own VPS — not deployed to Vercel
│   ├── honeypot.py           # SSH server — fake shell, tarpit, malware capture
│   ├── fake_fs.py            # stateful virtual filesystem + canary credentials
│   ├── threat_intel.py       # GeoIP, AbuseIPDB, Kaspersky OpenTIP, attack classification
│   ├── database.py           # SQLite access layer
│   ├── auth.py                # login, JWT sessions, password hashing
│   ├── alerts.py              # spike monitor + email/Discord/Slack/webhook notifications
│   ├── report_gen.py          # PDF report generation (reportlab)
│   ├── ws_server.py           # aiohttp API + WebSocket server, also serves dashboard.html
│   ├── seed_logs.py           # generates ~14 days of realistic demo data
│   ├── check_kaspersky_key.py # standalone script to sanity-check an OpenTIP API key
│   ├── dashboard.html         # same dashboard as index.html, for local dev via ws_server.py
│   ├── requirements.txt
│   ├── setup_and_run_v2.ps1   # Windows one-shot setup + launch
│   └── setup_and_run_v2.bat
└── README.md
```

`backend/logs/` (the SQLite database and its WAL files) and
`backend/__pycache__/` are runtime-generated and gitignored — don't expect
to find committed sample data there; `seed_logs.py` creates it.

---

## Features

- **SQLite database** (`backend/logs/honeypot.db`) — `sessions`,
  `auth_attempts`, `commands`, `suspicious_events`, `malware_captures`,
  `ip_reputation`, all indexed for the dashboard's queries.
- **Stateful fake shell** — tracks a working directory, handles `cd`/`ls`/
  `cat`/`echo`/`mkdir`/`touch`/`rm`, and serves realistic output for `ps`,
  `uptime`, `netstat`, `df`, `free`, and dozens of other commands.
- **Canary/deception credentials** planted in the fake filesystem
  (`/root/.aws/credentials`, `/root/.ssh/id_rsa`, `/root/.env`,
  `/var/www/html/wp-config.php`, etc.) to see exactly what attackers go
  looking for.
- **Tarpit delays** (0.2–0.8s per command, 0.5–2.0s per auth attempt) to
  waste automated brute-force tooling's time.
- **Real malware capture** — if an attacker's `wget`/`curl` points at a live
  URL, the honeypot actually fetches and SHA-256-hashes the payload.
- **GeoIP enrichment** via ip-api.com — country, city, ISP, ASN, lat/lon,
  cached 24h.
- **AbuseIPDB integration** (optional, free API key) — abuse confidence
  score, Tor exit-node detection.
- **Kaspersky OpenTIP integration** (optional, free API key from
  [opentip.kaspersky.com/token](https://opentip.kaspersky.com/token)) —
  Red/Orange/Yellow/Grey/Green threat zone per IP. When both AbuseIPDB and
  OpenTIP are configured, the *higher* of the two scores wins, so either
  source alone is enough to flag an IP as high-risk.
- **Attack pattern classification** — each login attempt is tagged
  `dictionary_attack`, `targeted_bruteforce`, `credential_stuffing`,
  `botnet_sweep`, or generic `bruteforce`, based on a sliding window of
  recent attempts.
- **Suspicious-command detection** — pattern-matches shell input for file
  downloads, reverse shells, persistence (`crontab`, `/etc/rc.local`),
  lateral movement, data exfiltration, and more, each tagged with a severity.
- **Alerting** — email, Discord, Slack, and generic webhook notifications on
  critical events, spike detection, and successful (honeypot) logins, with
  per-alert-type cooldowns to avoid flooding.
- **PDF threat reports** generated on demand from the live database.
- **Live WebSocket feed** when connected to a real `ws_server.py` backend;
  polling fallback otherwise.
- **Six dashboard views**: Overview, World Map, Credentials, Activity,
  Threats, Malware.

### Configuring the backend

Threat-intel API keys are read from environment variables so you don't have
to commit secrets to git:

```bash
export ABUSEIPDB_KEY="your_abuseipdb_key"        # abuseipdb.com/api — free tier: 1000/day
export KASPERSKY_OPENTIP_KEY="your_opentip_key"   # opentip.kaspersky.com/token — free
```

Both are optional and independent — set either, both, or neither. Sanity
check an OpenTIP key on its own, without touching the honeypot database:

```bash
export KASPERSKY_OPENTIP_KEY="your_opentip_key"
python check_kaspersky_key.py 8.8.8.8
```

Discord alert webhook and honeypot port are set directly in the source for
now:

```python
# backend/alerts.py — used by the CONFIG dict's discord_webhook, or set
# DISCORD_WEBHOOK / SLACK_WEBHOOK / WEBHOOK_URL as environment variables instead
```

```python
# backend/honeypot.py
PORT = 2222   # change to 22 for production — requires root or authbind
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

## Local development

```bash
cd backend
pip install -r requirements.txt
python seed_logs.py
python ws_server.py     # serves the dashboard itself at http://localhost:<port>
# in another terminal:
python honeypot.py
```

`ws_server.py` prints the port it bound (it tries 8080 first, then falls
back through a short list of alternates, then a random free port) — open
that URL, not `dashboard.html` as a file. Run `python -m pyflakes backend/*.py
api/*.py` before committing changes; the codebase is lint-clean and CI-worthy
as of this revision.

---

## Legal notice

Deploy the honeypot only on infrastructure you own or are explicitly
authorized to use for security research. Collecting honeypot traffic is
generally legitimate, but you're responsible for complying with local laws on
network monitoring and data retention.
