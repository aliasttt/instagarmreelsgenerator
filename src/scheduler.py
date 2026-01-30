"""
Daily scheduler: run pipeline once per day between 21:00–23:00 Turkey time.
Designed to run as a long-lived process (e.g. started at login) or via Windows Task Scheduler.
"""
import random
import time
from datetime import datetime, timedelta

import pytz

from src.config_loader import load_config
from src.pipeline import run_pipeline


def _parse_time(s: str) -> tuple[int, int]:
    """Parse 'HH:MM' -> (hour, minute)."""
    parts = s.strip().split(":")
    h = int(parts[0]) if parts else 21
    m = int(parts[1]) if len(parts) > 1 else 0
    return h, m


def _in_window(now: datetime, tz_name: str, start: str, end: str) -> bool:
    """True if now is between start and end (Turkey time)."""
    tz = pytz.timezone(tz_name)
    local = now.astimezone(tz)
    h_start, m_start = _parse_time(start)
    h_end, m_end = _parse_time(end)
    now_m = local.hour * 60 + local.minute
    start_m = h_start * 60 + m_start
    end_m = h_end * 60 + m_end
    return start_m <= now_m <= end_m


def run_scheduler(
    *,
    once: bool = False,
    config: dict | None = None,
) -> None:
    """
    Run scheduler: every minute check if we're in 21:00–23:00 Turkey time.
    If yes, run pipeline once. If once=True, exit after one run. Otherwise repeat daily.
    """
    if config is None:
        config = load_config()

    project = config.get("project", {})
    posting = config.get("posting", {})
    tz_name = project.get("timezone", "Europe/Istanbul")
    start = posting.get("time_start", "21:00")
    end = posting.get("time_end", "23:00")

    print(f"[Scheduler] Timezone: {tz_name}, window: {start}–{end}")
    if once:
        print("[Scheduler] Mode: run once at next window then exit")
    else:
        print("[Scheduler] Mode: run daily (Ctrl+C to stop)")

    last_run_date = None

    while True:
        now = datetime.now(pytz.UTC)
        today = now.astimezone(pytz.timezone(tz_name)).date()

        if _in_window(now, tz_name, start, end):
            if last_run_date != today:
                print("[Scheduler] Running pipeline...")
                try:
                    run_pipeline(config=config)
                    last_run_date = today
                except Exception as e:
                    print(f"[Scheduler] Pipeline error: {e}")
                if once:
                    return
                time.sleep(120)  # Don't re-run in same window
            else:
                time.sleep(60)
        else:
            time.sleep(60)
