"""
Fully automated daily pipeline (no UI, no prompts).
Output: output/reels/reel_YYYY-MM-DD.mp4, output/captions/caption_YYYY-MM-DD.txt
Logs: logs/daily.log
Prevents double-run on same day.
"""
import sys
from pathlib import Path
from datetime import datetime

import pytz

# Ensure project root is on path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.config_loader import load_config, get_project_root
from src.text_generator import generate_sentence
from src.video_creator import create_reel
from src.caption_generator import (
    generate_caption_and_hashtags,
    save_caption_to_path,
)
from src.logger import write_log, log_success, log_error, log_skip


def _today_turkey(config: dict) -> str:
    """Return today's date in Turkey timezone as YYYY-MM-DD."""
    tz_name = config.get("project", {}).get("timezone", "Europe/Istanbul")
    tz = pytz.timezone(tz_name)
    now = datetime.now(tz)
    return now.strftime("%Y-%m-%d")


def run_pipeline(
    *,
    config: dict | None = None,
) -> dict:
    """
    Run full pipeline once. No UI. No prompts.
    - If reel_YYYY-MM-DD.mp4 already exists: skip and log.
    - Else: generate text, download video/music, create reel, save caption, log.
    Returns dict with keys: ran, sentence, video_path, caption_path, error.
    """
    if config is None:
        config = load_config()

    root = get_project_root()
    paths = config["paths"]
    out_reels = root / paths["output_reels"]
    out_captions = root / paths["captions_dir"]
    date_str = _today_turkey(config)
    video_path = out_reels / f"reel_{date_str}.mp4"
    caption_path = out_captions / f"caption_{date_str}.txt"

    result = {
        "ran": False,
        "sentence": "",
        "video_path": None,
        "caption_path": None,
        "error": None,
    }

    # Prevent double-run: if today's reel exists, skip
    if video_path.exists():
        log_skip(f"Already run today: {video_path.name}", config=config)
        result["video_path"] = str(video_path)
        result["caption_path"] = str(caption_path) if caption_path.exists() else None
        return result

    write_log("Pipeline started", config=config)

    try:
        # 1. Generate viral text
        content_cfg = config.get("content", {}).get("distribution", {}) or {
            "emotional": 0.40,
            "sarcastic": 0.30,
            "deep": 0.20,
            "romantic": 0.10,
        }
        sentence, content_category = generate_sentence(distribution=content_cfg, return_category=True)
        result["sentence"] = sentence

        # 2 + 3 + 4. Download background video, download music (matching mood), create reel
        out_reels.mkdir(parents=True, exist_ok=True)
        create_reel(sentence, output_path=video_path, config=config, content_category=content_category)
        result["video_path"] = str(video_path)

        # 5. Generate caption and hashtags
        caption, hashtag_line = generate_caption_and_hashtags(sentence, config=config)
        full_text = caption + "\n\n" + hashtag_line

        # 6. Save outputs
        out_captions.mkdir(parents=True, exist_ok=True)
        save_caption_to_path(full_text, caption_path)
        result["caption_path"] = str(caption_path)

        # 7. Log success
        log_success(str(video_path), str(caption_path), config=config)
        result["ran"] = True
        return result

    except Exception as e:
        err_msg = str(e)
        log_error(err_msg, config=config)
        result["error"] = err_msg
        return result


if __name__ == "__main__":
    run_pipeline()
