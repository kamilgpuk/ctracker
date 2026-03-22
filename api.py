"""
Fetches Claude Code usage from claude.ai internal API.
Uses curl_cffi to impersonate Chrome's TLS fingerprint (required to bypass Cloudflare).
Uses browser_cookie3 to read fresh cookies from Chrome automatically.
No config file needed — org_id is read from the lastActiveOrg cookie.
"""

from datetime import datetime, timezone
import browser_cookie3
from curl_cffi import requests


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

    resp = requests.get(url, cookies=cookies, headers=headers, impersonate="chrome120", timeout=10)
    resp.raise_for_status()
    return resp.json()


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
