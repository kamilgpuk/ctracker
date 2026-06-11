"""
Fetches Claude Code usage from claude.ai internal API.
Uses curl_cffi to impersonate Chrome's TLS fingerprint (required to bypass Cloudflare).
Uses browser_cookie3 to read fresh cookies from Chrome automatically.
No config file needed — org_id is read from the lastActiveOrg cookie.
"""

from datetime import datetime, timezone
import os
import glob
import time
import browser_cookie3
from curl_cffi import requests

MAX_RETRIES = 3
BACKOFF_BASE = 2  # seconds

CHROME_DIR = os.path.expanduser("~/Library/Application Support/Google/Chrome")


def _profile_cookie_files():
    """All Chrome profile cookie stores, most recently used first.

    Chrome keeps separate cookies per profile (Default, Profile 1, Profile 2…).
    We don't know which profile is logged into claude.ai, so we list them all
    and let the caller pick the one with an active session.
    """
    candidates = []
    for profile_dir in glob.glob(os.path.join(CHROME_DIR, "*")):
        for name in ("Network/Cookies", "Cookies"):  # newer Chrome uses Network/
            path = os.path.join(profile_dir, name)
            if os.path.exists(path):
                candidates.append(path)
                break
    candidates.sort(key=os.path.getmtime, reverse=True)
    return candidates


def _read_claude_cookies():
    """Return cookies from whichever Chrome profile is logged into claude.ai.

    Picks the most recently used profile that has both a sessionKey and a
    lastActiveOrg — i.e. a real logged-in session. Set CTRACKER_CHROME_PROFILE
    (e.g. "Profile 1") to force a specific profile.
    """
    override = os.environ.get("CTRACKER_CHROME_PROFILE")
    if override:
        for name in ("Network/Cookies", "Cookies"):
            path = os.path.join(CHROME_DIR, override, name)
            if os.path.exists(path):
                cj = browser_cookie3.chrome(domain_name=".claude.ai", cookie_file=path)
                return {c.name: c.value for c in cj}

    last_error = None
    for cookie_file in _profile_cookie_files():
        try:
            cj = browser_cookie3.chrome(domain_name=".claude.ai", cookie_file=cookie_file)
            cookies = {c.name: c.value for c in cj}
        except Exception as e:
            last_error = e
            continue
        if cookies.get("sessionKey") and cookies.get("lastActiveOrg"):
            return cookies

    # Nothing logged in: fall back to default profile so the usual error surfaces.
    if last_error:
        raise last_error
    return {c.name: c.value for c in browser_cookie3.chrome(domain_name=".claude.ai")}


def _get_cookies_and_org():
    cookies = _read_claude_cookies()
    org_id = cookies.get("lastActiveOrg")
    if not org_id:
        raise Exception("Nie znaleziono aktywnej sesji claude.ai w żadnym profilu Chrome. Zaloguj się na claude.ai w Chrome.")
    return cookies, org_id


def _api_get(url, cookies, referer):
    headers = {
        "Accept": "application/json",
        "Referer": referer,
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


def get_usage():
    cookies, org_id = _get_cookies_and_org()
    url = f"https://claude.ai/api/organizations/{org_id}/usage"
    return _api_get(url, cookies, "https://claude.ai/settings/usage")


def get_extra_usage():
    """Fetch extra usage (overage) spend data. Returns dict or None on failure."""
    try:
        cookies, org_id = _get_cookies_and_org()
        url = f"https://claude.ai/api/organizations/{org_id}/overage_spend_limit"
        data = _api_get(url, cookies, "https://claude.ai/settings/billing")

        if not data.get("is_enabled"):
            return {"enabled": False, "used": 0, "limit": 0, "currency": "USD"}

        # API returns values in cents — convert to base currency units
        return {
            "enabled": True,
            "used": float(data.get("used_credits", 0)) / 100.0,
            "limit": float(data.get("monthly_credit_limit", 0)) / 100.0,
            "currency": (data.get("currency") or "USD").upper(),
        }
    except Exception:
        return None


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
