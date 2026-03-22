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

ctracker is a lightweight, read-only monitor. Here's the full data flow:

1. **Cookie reading** — On each refresh, `browser_cookie3` reads three cookies from your local Chrome storage: `sessionKey` (your login session), `cf_clearance` (Cloudflare token), and `lastActiveOrg` (your organization ID). This requires one-time Keychain approval from macOS.

2. **API call** — The app makes a single `GET` request to `https://claude.ai/api/organizations/{org_id}/usage`. This is the same endpoint your browser hits when you open Settings → Usage on claude.ai. It uses `curl_cffi` to match Chrome's TLS fingerprint, which is required to pass Cloudflare's bot detection.

3. **Display** — The JSON response contains `five_hour.utilization` and `seven_day.utilization` (floats 0–1) plus `resets_at` timestamps. The app formats these as percentages and countdowns, then renders them in the macOS menu bar via `rumps`.

4. **Repeat** — A background timer fires every 120 seconds. On failure, the app retries up to 3 times with exponential backoff (2s, 4s) before showing an error icon.

That's it. No background services, no databases, no accounts to create.

## Security

This app was designed to be safe to run and easy to audit. The entire codebase is ~100 lines across two files.

### What the app does NOT do

- **No credentials stored** — Zero API keys, tokens, or passwords in the code or on disk. Authentication is delegated entirely to your existing Chrome session.
- **No data written to disk** — No databases, no cache files, no state files. The only file output is `error.log` (error messages only, no sensitive data).
- **No data sent anywhere** — The app talks to exactly one endpoint (`claude.ai`), using your own cookies. Nothing is sent to third-party servers, analytics, or telemetry services.
- **No code execution** — No `eval()`, `exec()`, `subprocess`, or shell commands anywhere in the codebase.
- **No write operations** — Only `GET` requests. The app cannot modify your account, settings, or usage.

### What the app DOES do

- **Reads 3 Chrome cookies** — `sessionKey`, `cf_clearance`, `lastActiveOrg`. These stay in memory during the request and are never logged or persisted.
- **Makes HTTPS GET requests** — Read-only, to a single Anthropic endpoint, over TLS.
- **Displays text in your menu bar** — That's the entire output.

### Dependencies

Only 3 packages, all pinned to exact versions:

| Package | Version | What it does | Why it's needed |
|---------|---------|--------------|-----------------|
| `rumps` | 0.4.0 | macOS menu bar UI framework | Displays the utilization widget |
| `browser-cookie3` | 0.20.1 | Reads cookies from Chrome's local storage | Authenticates against claude.ai without asking for credentials |
| `curl-cffi` | 0.13.0 | HTTP client with TLS fingerprinting | Cloudflare requires a browser-like TLS handshake; standard `requests` gets blocked |

### Verify it yourself

The app is intentionally tiny so you can read every line before running it:

```bash
cat api.py   # ~60 lines — HTTP client
cat app.py   # ~50 lines — menu bar UI
```

### Keychain prompt

On first launch, macOS will show a dialog: *"python3 wants to access your Keychain."* This is `browser_cookie3` decrypting Chrome's cookie store (Chrome encrypts cookies via the macOS Keychain). You can click **Allow** (one-time) or **Always Allow**. If you deny it, the app won't work — it has no other way to authenticate.

## License

MIT
