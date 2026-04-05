#!/usr/bin/env python3
"""
ctracker — Claude Code usage in the macOS menu bar.
Shows session (5h window) and weekly token utilization %.
"""

import rumps
import os
import logging
import threading
from api import get_usage, get_extra_usage, format_resets_in

LOG_PATH = os.path.join(os.path.dirname(__file__), "error.log")
logging.basicConfig(filename=LOG_PATH, level=logging.ERROR,
                    format="%(asctime)s %(levelname)s %(message)s")


PREFS_PATH = os.path.join(os.path.dirname(__file__), ".ctracker_prefs")

CURRENCY_SYMBOLS = {
    "USD": "$", "EUR": "€", "GBP": "£", "PLN": "zł",
    "JPY": "¥", "CHF": "CHF", "CAD": "CA$", "AUD": "A$",
}


def pct(value):
    """Round to 1 decimal, drop .0 if whole number."""
    if value is None:
        return "?"
    v = round(float(value), 1)
    return f"{int(v)}%" if v == int(v) else f"{v}%"


def format_cost(amount, currency="USD"):
    """Format amount to a readable currency string."""
    symbol = CURRENCY_SYMBOLS.get(currency, currency + " ")
    if currency in ("PLN",):
        return f"{amount:.2f} {symbol}"
    return f"{symbol}{amount:.2f}"


def _load_pref_show_cost():
    try:
        with open(PREFS_PATH, "r") as f:
            return f.read().strip() == "1"
    except Exception:
        return False


def _save_pref_show_cost(enabled):
    try:
        with open(PREFS_PATH, "w") as f:
            f.write("1" if enabled else "0")
    except Exception:
        pass


class CTrackerApp(rumps.App):
    def __init__(self):
        super().__init__("CC …", quit_button=None)

        self.session_item = rumps.MenuItem("Sesja: ładowanie…")
        self.week_item = rumps.MenuItem("Tydzień: ładowanie…")
        self.cost_item = rumps.MenuItem("Extra usage: —")
        self.show_cost_item = rumps.MenuItem(
            "Pokaż extra usage",
            callback=self._toggle_show_cost,
        )
        self.refresh_item = rumps.MenuItem("Odśwież", callback=self.refresh)
        self.quit_item = rumps.MenuItem("Zamknij", callback=rumps.quit_application)

        self._show_cost = _load_pref_show_cost()
        self.show_cost_item.state = self._show_cost
        self._last_cost_text = ""

        self.menu = [
            self.session_item,
            self.week_item,
            None,
            self.cost_item,
            self.show_cost_item,
            None,
            self.refresh_item,
            None,
            self.quit_item,
        ]

        self._last_error = None
        self._timer = rumps.Timer(self._tick, 120)
        self._timer.start()
        # First fetch immediately in background
        threading.Thread(target=self._fetch_and_update, daemon=True).start()

    def _toggle_show_cost(self, sender):
        self._show_cost = not self._show_cost
        sender.state = self._show_cost
        _save_pref_show_cost(self._show_cost)
        # Update title immediately
        self._update_title()

    def _update_title(self):
        base = self._base_title if hasattr(self, '_base_title') else "CC …"
        if self._show_cost and self._last_cost_text:
            self.title = f"{base}  {self._last_cost_text}"
        else:
            self.title = base

    def _tick(self, _sender):
        threading.Thread(target=self._fetch_and_update, daemon=True).start()

    def _fetch_and_update(self):
        try:
            data = get_usage()

            session = data.get("five_hour", {}) or {}
            week = data.get("seven_day", {}) or {}

            s_pct = pct(session.get("utilization"))
            w_pct = pct(week.get("utilization"))

            s_resets = format_resets_in(session.get("resets_at", ""))
            w_resets = format_resets_in(week.get("resets_at", ""))

            # Base title (without cost)
            self._base_title = f"S:{s_pct} W:{w_pct}"

            # Dropdown details
            self.session_item.title = f"Sesja (5h):  {s_pct} — reset za {s_resets}"
            self.week_item.title = f"Tydzień:     {w_pct} — reset za {w_resets}"

            self._last_error = None

        except Exception as e:
            logging.error("Fetch failed: %s", e)
            self._base_title = "CC ⚠"
            self.session_item.title = f"Błąd: {e}"
            self.week_item.title = "Sprawdź połączenie z claude.ai"
            self._last_error = str(e)

        # Fetch extra usage (separate try — usage still works if this fails)
        try:
            extra = get_extra_usage()
            if extra and extra["enabled"]:
                used_str = format_cost(extra["used"], extra["currency"])
                limit_str = format_cost(extra["limit"], extra["currency"])
                self.cost_item.title = f"Extra usage: {used_str} / {limit_str}"
                self._last_cost_text = used_str
            elif extra and not extra["enabled"]:
                self.cost_item.title = "Extra usage: wyłączone"
                self._last_cost_text = ""
            else:
                self.cost_item.title = "Extra usage: niedostępne"
                self._last_cost_text = ""
        except Exception:
            self.cost_item.title = "Extra usage: niedostępne"
            self._last_cost_text = ""

        self._update_title()

    def refresh(self, _sender):
        self.title = "CC …"
        threading.Thread(target=self._fetch_and_update, daemon=True).start()


if __name__ == "__main__":
    CTrackerApp().run()
