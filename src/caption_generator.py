"""
Generates Turkish caption (1-2 short emotional lines) and 10-15 Turkish hashtags.
No spam or banned hashtags.
"""
import random
from pathlib import Path

from src.config_loader import get_project_root, load_config


# Short emotional Turkish caption lines (1-2 lines)
CAPTION_LINES = [
    "Gece düşüncelerin en derin olduğu an",
    "Bazen sessizlik en iyi cevap",
    "Her şey geçer izi kalır",
    "Yalnız değil yalnız hisseden var",
    "Gecenin bir yarısı aklına düşen",
    "Bazı şeyler kelimelerle anlatılmaz",
    "İçinde bir şeyler kırıldığında",
    "Gece uzadıkça düşünceler derinleşir",
    "Kimse senin yükünü taşımaz",
    "Bazen en sessiz insanlar en çok acı çeker",
    "Her şey geçer ama izi kalır",
    "Gülümsemek en kolay yalan",
    "İçindeki fırtınayı kimse görmez",
    "Gece olunca her şey daha ağır",
    "Kaybetmek değil alışmak zor",
    "Bazı yaralar görünmez hep kanar",
    "Yorgunluk bazen yürekten gelir",
    "Bazen susmak en iyi cevap",
    "En çok güvendiğin en çok incitir",
    "Gece düşüncelerin seni bulduğu zaman",
]

# Turkish hashtags - trending, emotional, not spam/banned
HASHTAG_POOL = [
    "keşfet",
    "duygular",
    "yalnızlık",
    "hayathalleri",
    "gece",
    "istanbul",
    "sözler",
    "ruh",
    "düşünce",
    "gecehali",
    "akşam",
    "melankoli",
    "hisler",
    "an",
    "yaşam",
    "hayat",
    "kalp",
    "gecepaylaşımları",
    "reels",
    "reel",
    "türkiye",
    "ankara",
    "izmir",
    "gecevakti",
    "sessizlik",
    "düşünceler",
    "paylaşım",
    "içsel",
    "geceklibi",
    "motivasyon",
    "söz",
    "alıntı",
    "etkileyici",
    "derin",
    "anlamlı",
]


def generate_caption(sentence: str, config: dict | None = None) -> str:
    """
    Generate 1-2 short emotional Turkish caption lines.
    Does not include the main sentence (that's on the video).
    """
    count = random.choice([1, 2])
    lines = random.sample(CAPTION_LINES, min(count, len(CAPTION_LINES)))
    return "\n".join(lines)


def generate_hashtags(count: int = 12, config: dict | None = None) -> list[str]:
    """Generate 10-15 Turkish hashtags from pool. Avoid duplicates."""
    count = max(10, min(15, count))
    return list(dict.fromkeys(["#" + h for h in random.sample(HASHTAG_POOL, min(count, len(HASHTAG_POOL)))]))


def generate_caption_and_hashtags(
    sentence: str,
    config: dict | None = None,
) -> tuple[str, str]:
    """
    Returns (full_caption, hashtag_line).
    full_caption = caption lines only (no hashtags).
    hashtag_line = space-separated hashtags for pasting in second line or comment.
    """
    if config is None:
        config = load_config()
    caption = generate_caption(sentence, config)
    hashtags = generate_hashtags(random.randint(10, 15), config)
    hashtag_line = " ".join(hashtags)
    return caption, hashtag_line


def save_caption(
    full_text: str,
    reel_name: str,
    config: dict | None = None,
) -> Path:
    """Save caption + hashtags to output/captions for reference."""
    if config is None:
        config = load_config()
    root = get_project_root()
    cap_dir = root / config["paths"]["captions_dir"]
    cap_dir.mkdir(parents=True, exist_ok=True)
    path = cap_dir / f"{reel_name}_caption.txt"
    path.write_text(full_text, encoding="utf-8")
    return path


def save_caption_to_path(full_text: str, path: Path) -> Path:
    """Save caption + hashtags to the given path (e.g. caption_YYYY-MM-DD.txt)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(full_text, encoding="utf-8")
    return path
