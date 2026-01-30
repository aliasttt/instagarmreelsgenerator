"""
Build a new Reel with:
- Text backdrop (readable on any video)
- Music from Pixabay (same API key as video), varied each run, matched to text mood
- Background video from Pexels/Pixabay matched to text mood

Each run ADDS a new file. Reel and caption use the SAME number (۱، ۲، ۳، …) so you know which reel goes with which caption.
Usage:
  python build_reel.py   -> output/reels/1.mp4 + output/captions/1.txt (then 2, 3, …)
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config_loader import load_config
from src.text_generator import generate_sentence
from src.video_creator import create_reel
from src.caption_generator import generate_caption_and_hashtags, save_caption_to_path


def _next_number(reels_dir: Path, captions_dir: Path) -> int:
    """Find next free number from existing 1.mp4, 2.mp4, 1.txt, 2.txt, …"""
    used = set()
    for d, ext in ((reels_dir, ".mp4"), (captions_dir, ".txt")):
        if not d.exists():
            continue
        for f in d.iterdir():
            if f.suffix.lower() != ext:
                continue
            stem = f.stem
            if re.match(r"^\d+$", stem):
                used.add(int(stem))
    return max(used, default=0) + 1


def main():
    config = load_config()
    reels_dir = ROOT / config.get("paths", {}).get("output_reels", "output/reels")
    captions_dir = ROOT / config.get("paths", {}).get("captions_dir", "output/captions")
    reels_dir.mkdir(parents=True, exist_ok=True)
    captions_dir.mkdir(parents=True, exist_ok=True)

    n = _next_number(reels_dir, captions_dir)
    out_path = reels_dir / f"{n}.mp4"
    caption_path = captions_dir / f"{n}.txt"

    content_cfg = config.get("content", {}).get("distribution", {}) or {
        "emotional": 0.4, "sarcastic": 0.3, "deep": 0.2, "romantic": 0.1
    }
    sentence, category = generate_sentence(distribution=content_cfg, return_category=True)

    print("Number:", n)
    print("Category:", category)
    print("Creating reel (text backdrop + new music by mood)...")
    p = create_reel(sentence, output_path=out_path, config=config, content_category=category)
    print("Reel:", str(p))

    caption, hashtag_line = generate_caption_and_hashtags(sentence, config=config)
    save_caption_to_path(caption + "\n\n" + hashtag_line, caption_path)
    print("Caption:", str(caption_path))


if __name__ == "__main__":
    main()
