"""
Fully automated daily entry. No UI. No prompts. No user interaction.
Task Scheduler -> run_daily.bat -> this script -> full pipeline -> exit.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.pipeline import run_pipeline
from src.config_loader import load_config


def main() -> None:
    config = load_config()
    run_pipeline(config=config)


if __name__ == "__main__":
    main()
    sys.exit(0)
