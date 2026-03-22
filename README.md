# ctracker

macOS menu bar app that shows your Claude Code API usage in real time.

![menu bar](https://img.shields.io/badge/macOS-menu%20bar-black)
![python](https://img.shields.io/badge/python-3.9+-blue)
![license](https://img.shields.io/badge/license-MIT-green)

## What it does

- **Session (5h)** — current 5-hour window utilization %
- **Weekly (7d)** — rolling 7-day utilization %
- Countdown to next reset
- Auto-refreshes every 2 minutes

No API keys needed — reads your existing Chrome session cookies automatically.

## Install

```bash
git clone https://github.com/kamilgpuk/ctracker.git
cd ctracker
pip3 install -r requirements.txt
```

### First run

```bash
python3 app.py
```

macOS will ask for Keychain access (to read Chrome cookies) — click **Allow**.

## Build as .app

```bash
pip3 install py2app
python3 setup.py py2app
```

The app bundle appears at `dist/ctracker.app`. Drag it to Applications or add to Login Items for auto-start.

## Requirements

- macOS
- Python 3.9+
- Chrome with an active [claude.ai](https://claude.ai) session

## How it works

1. Reads `sessionKey` and `cf_clearance` cookies from Chrome via `browser_cookie3`
2. Fetches usage data from `claude.ai/api/organizations/{org_id}/usage`
3. Displays utilization % in the menu bar via `rumps`

Uses `curl_cffi` for TLS fingerprint impersonation (required to pass Cloudflare).

## License

MIT
