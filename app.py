#!/usr/bin/env python3
"""
ctracker — Claude Code usage in the macOS menu bar.
Shows session (5h window) and weekly token utilization %.
"""

import rumps
import os
import logging
import threading
from api import get_usage, format_resets_in

LOG_PATH = os.path.join(os.path.dirname(__file__), "error.log")
logging.basicConfig(filename=LOG_PATH, level=logging.ERROR,
                    format="%(asctime)s %(levelname)s %(message)s")


def pct(value):
    """Round to 1 decimal, drop .0 if whole number."""
    if value is None:
        return "?"
    v = round(float(value), 1)
    return f"{int(v)}%" if v == int(v) else f"{v}%"


class CTrackerApp(rumps.App):
    def __init__(self):
        super().__init__("CC …", quit_button=None)

        self.session_item = rumps.MenuItem("Sesja: ładowanie…")
        self.week_item = rumps.MenuItem("Tydzień: ładowanie…")
        separator = rumps.separator
        self.refresh_item = rumps.MenuItem("Odśwież", callback=self.refresh)
        self.quit_item = rumps.MenuItem("Zamknij", callback=rumps.quit_application)

        self.menu = [
            self.session_item,
            self.week_item,
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

            # Menu bar title
            self.title = f"S:{s_pct} W:{w_pct}"

            # Dropdown details
            self.session_item.title = f"Sesja (5h):  {s_pct} — reset za {s_resets}"
            self.week_item.title = f"Tydzień:     {w_pct} — reset za {w_resets}"

            self._last_error = None

        except Exception as e:
            logging.error("Fetch failed: %s", e)
            self.title = "CC ⚠"
            self.session_item.title = f"Błąd: {e}"
            self.week_item.title = "Sprawdź połączenie z claude.ai"
            self._last_error = str(e)

    def refresh(self, _sender):
        self.title = "CC …"
        threading.Thread(target=self._fetch_and_update, daemon=True).start()


if __name__ == "__main__":
    CTrackerApp().run()
