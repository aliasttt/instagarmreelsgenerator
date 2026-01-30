"""
Daily pipeline logging. Writes to logs/daily.log (append).
No UI. No prompts.
"""
from pathlib import Path
from datetime import datetime

from src.config_loader import get_project_root, load_config


def _log_dir(config: dict | None = None) -> Path:
    if config is None:
        config = load_config()
    root = get_project_root()
    logs_dir = root / config["paths"]["logs_dir"]
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def write_log(
    message: str,
    level: str = "INFO",
    config: dict | None = None,
) -> None:
    """Append one line to logs/daily.log. No console output."""
    logs_dir = _log_dir(config)
    log_file = logs_dir / "daily.log"
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{ts} [{level}] {message}\n"
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass


def log_success(video_path: str, caption_path: str, config: dict | None = None) -> None:
    """Log successful pipeline run."""
    write_log(f"SUCCESS | video={video_path} | caption={caption_path}", level="INFO", config=config)


def log_error(message: str, config: dict | None = None) -> None:
    """Log pipeline error."""
    write_log(f"ERROR | {message}", level="ERROR", config=config)


def log_skip(reason: str, config: dict | None = None) -> None:
    """Log skip (e.g. already run today)."""
    write_log(f"SKIP | {reason}", level="INFO", config=config)
