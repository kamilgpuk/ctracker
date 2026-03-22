"""
Fetches Claude Code usage from claude.ai internal API.
Uses curl_cffi to impersonate Chrome's TLS fingerprint (required to bypass Cloudflare).
Uses browser_cookie3 to read fresh cookies from Chrome automatically.
No config file needed — org_id is read from the lastActiveOrg cookie.
"""

from datetime import datetime, timezone
import time
import browser_cookie3
from curl_cffi import requests

MAX_RETRIES = 3
BACKOFF_BASE = 2  # seconds


def get_usage():
    cookies = {c.name: c.value for c in browser_cookie3.chrome(domain_name=".claude.ai")}

    org_id = cookies.get("lastActiveOrg")
    if not org_id:
        raise Exception("Nie znaleziono lastActiveOrg w cookies Chrome. Zaloguj się na claude.ai w Chrome.")

    url = f"https://claude.ai/api/organizations/{org_id}/usage"

    headers = {
        "Accept": "application/json",
        "Referer": "https://claude.ai/settings/usage",
    }

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(url, cookies=cookies, headers=headers, impersonate="chrome120", timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                time.sleep(BACKOFF_BASE ** (attempt + 1))
    raise last_error


def format_resets_in(resets_at_str):
    """Return human-readable time until reset, e.g. '3h 56m'"""
    try:
        resets_at = datetime.fromisoformat(resets_at_str)
        now = datetime.now(timezone.utc)
        delta = resets_at - now
        if delta.total_seconds() <= 0:
            return "resetuje się…"
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes = remainder // 60
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"
    except Exception:
        return "?"
