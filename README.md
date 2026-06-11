# ctracker

macOS menu bar app that shows your Claude Code API usage in real time.

![menu bar](https://img.shields.io/badge/macOS-menu%20bar-black)
![python](https://img.shields.io/badge/python-3.9+-blue)
![license](https://img.shields.io/badge/license-MIT-green)

<img width="464" height="106" alt="CleanShot 2026-03-24 at 15 33 30@2x" src="https://github.com/user-attachments/assets/dc18ffff-4473-4d1a-a93b-c2468aad75e1" />

## What it does

- **Session (5h)** — current 5-hour window utilization %
- **Weekly (7d)** — rolling 7-day utilization %
- **Extra usage cost** — optional display of overage spend in your currency (EUR, USD, etc.)
- **Multi-profile support** — automatically finds the Chrome profile that's logged into claude.ai, so it works on shared Macs and with multiple Chrome profiles
- Countdown to next reset
- Auto-refreshes every 2 minutes

No API keys needed — reads your existing Chrome session cookies automatically.

## Install

```bash
git clone https://github.com/kamilgpuk/ctracker.git
cd ctracker
pip3 install -r requirements.txt
```

> **`pip3` fails with `externally-managed-environment`?** That's [PEP 668](https://peps.python.org/pep-0668/) on newer Python (e.g. Homebrew). Use a virtual environment instead:
>
> ```bash
> python3 -m venv .venv
> source .venv/bin/activate
> pip install -r requirements.txt
> ```
>
> Keep it activated (or prefix the commands below with `.venv/bin/`) when you run or build the app.

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
- Chrome with an active [claude.ai](https://claude.ai) session (in any profile)

## How it works

ctracker is a lightweight, read-only monitor. Here's the full data flow:

1. **Cookie reading** — On each refresh, the app scans all your Chrome profiles (Default, Profile 1, …) and picks the most recently used one with an active claude.ai session. From it, `browser_cookie3` reads three cookies: `sessionKey` (your login session), `cf_clearance` (Cloudflare token), and `lastActiveOrg` (your organization ID). This requires one-time Keychain approval from macOS.

2. **API calls** — The app makes two `GET` requests: `/usage` (session & weekly utilization) and `/overage_spend_limit` (extra usage cost). These are the same endpoints your browser hits on claude.ai Settings. It uses `curl_cffi` to match Chrome's TLS fingerprint, which is required to pass Cloudflare's bot detection. If the billing endpoint fails, usage data still works normally.

3. **Display** — The JSON response contains `five_hour.utilization` and `seven_day.utilization` (floats 0–1) plus `resets_at` timestamps. The app formats these as percentages and countdowns, then renders them in the macOS menu bar via `rumps`.

4. **Repeat** — A background timer fires every 120 seconds. On failure, the app retries up to 3 times with exponential backoff (2s, 4s) before showing an error icon.

That's it. No background services, no databases, no accounts to create.

## Multiple Chrome profiles

If you use several Chrome profiles (e.g. work and personal), ctracker automatically follows the right one: on every refresh it picks the most recently used profile that has an active claude.ai session (`sessionKey` + `lastActiveOrg` cookies). Log into claude.ai on a different profile and the app switches to it on the next refresh — no configuration needed.

To pin a specific profile instead, set `CTRACKER_CHROME_PROFILE` to the profile's directory name (`Default`, `Profile 1`, `Profile 2`, …):

```bash
CTRACKER_CHROME_PROFILE="Profile 1" python3 app.py
```

The app also keeps its own files out of the app bundle, so a `.app` installed in `/Applications` works for every user on the Mac:

- error log → `~/Library/Logs/ctracker/error.log`
- preferences → `~/Library/Application Support/ctracker/.ctracker_prefs`

## Security

This app was designed to be safe to run and easy to audit. The entire codebase is ~300 lines across two files.

### What the app does NOT do

- **No credentials stored** — Zero API keys, tokens, or passwords in the code or on disk. Authentication is delegated entirely to your existing Chrome session.
- **No sensitive data written to disk** — The only files written are an error log (`~/Library/Logs/ctracker/error.log`, error messages only) and a one-byte preference file (`~/Library/Application Support/ctracker/.ctracker_prefs`, a single `0` or `1` for the extra usage toggle). No databases, no cache files.
- **No data sent anywhere** — The app talks only to `claude.ai` endpoints, using your own cookies. Nothing is sent to third-party servers, analytics, or telemetry services.
- **No code execution** — No `eval()`, `exec()`, `subprocess`, or shell commands anywhere in the codebase.
- **No write operations** — Only `GET` requests. The app cannot modify your account, settings, or usage.

### What the app DOES do

- **Reads 3 Chrome cookies** — `sessionKey`, `cf_clearance`, `lastActiveOrg`. These stay in memory during the request and are never logged or persisted.
- **Makes HTTPS GET requests** — Read-only, to two Anthropic endpoints (`/usage` and `/overage_spend_limit`), over TLS.
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
cat api.py   # ~140 lines — HTTP client + Chrome profile discovery
cat app.py   # ~175 lines — menu bar UI
```

### Keychain prompt

On first launch, macOS will show a dialog: *"python3 wants to access your Keychain."* This is `browser_cookie3` decrypting Chrome's cookie store (Chrome encrypts cookies via the macOS Keychain). You can click **Allow** (one-time) or **Always Allow**. If you deny it, the app won't work — it has no other way to authenticate.

## License

MIT
