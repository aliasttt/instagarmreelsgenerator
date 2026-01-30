"""
Auto-download aesthetic background videos from Pexels and Pixabay.
Saves to assets/cache/videos. Reuses cache when possible.
"""
import os
import random
import re
import time
from pathlib import Path
from urllib.parse import quote_plus

import requests

from src.config_loader import get_project_root, load_config


def _log(msg: str) -> None:
    print(f"[DownloadVideo] {msg}")


def _pexels_search(api_key: str, query: str, orientation: str = "portrait", per_page: int = 15) -> list[dict]:
    """Search Pexels Videos API. Returns list of video dicts with video_files."""
    if not api_key or not api_key.strip():
        return []
    url = "https://api.pexels.com/videos/search"
    params = {"query": query, "per_page": per_page, "orientation": orientation}
    headers = {"Authorization": api_key.strip()}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=15)
        r.raise_for_status()
        data = r.json()
        return data.get("videos") or []
    except Exception as e:
        _log(f"Pexels search failed: {e}")
        return []


def _pexels_best_download_url(video: dict, prefer_portrait: bool = True) -> str | None:
    """Pick best MP4 link from Pexels video (prefer portrait, then HD)."""
    files = video.get("video_files") or []
    mp4 = [f for f in files if f.get("file_type") == "video/mp4" and f.get("link")]
    if not mp4:
        return None
    width = video.get("width") or 0
    height = video.get("height") or 0
    # Prefer portrait (height > width)
    if prefer_portrait:
        portrait = [f for f in mp4 if f.get("height", 0) > f.get("width", 0)]
        if portrait:
            # Prefer 1080x1920 or closest
            best = max(portrait, key=lambda f: min(f.get("height", 0), f.get("width", 0)))
            return best.get("link")
    # Else take HD
    best = max(mp4, key=lambda f: (f.get("width", 0) or 0) + (f.get("height", 0) or 0))
    return best.get("link")


def _pixabay_search(api_key: str, query: str, per_page: int = 15) -> list[dict]:
    """Search Pixabay Videos API. Returns list of hits with videos (large/medium/small)."""
    if not api_key or not api_key.strip():
        return []
    url = "https://pixabay.com/api/videos/"
    params = {"key": api_key.strip(), "q": query, "per_page": per_page}
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        return data.get("hits") or []
    except Exception as e:
        _log(f"Pixabay search failed: {e}")
        return []


def _pixabay_best_download_url(hit: dict) -> str | None:
    """Pick best MP4 URL from Pixabay hit. Prefer medium or large."""
    videos = hit.get("videos") or {}
    for key in ("medium", "large", "small"):
        v = videos.get(key)
        if v and isinstance(v, dict) and v.get("url"):
            return v["url"]
    return None


def _download_file(url: str, dest: Path) -> bool:
    """Download URL to dest. Returns True on success."""
    try:
        r = requests.get(url, stream=True, timeout=60)
        r.raise_for_status()
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        _log(f"Download failed {url[:50]}...: {e}")
        return False


def _safe_filename(name: str) -> str:
    """Make a safe filename (alphanumeric, dash, underscore)."""
    name = re.sub(r"[^\w\-.]", "_", name)
    return name[:80] or "video"


def download_background_video(config: dict | None = None) -> Path:
    """
    Download one aesthetic background video to cache.
    Tries Pexels first (portrait), then Pixabay. Reuses cache if already has enough files.
    Returns path to the downloaded (or existing cached) video file.
    """
    if config is None:
        config = load_config()
    root = get_project_root()
    cache_dir = root / config["paths"]["cache_videos"]
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Check cache: use existing if we have at least 3 files (reuse)
    exts = (".mp4", ".mov", ".webm")
    cached = [f for f in cache_dir.iterdir() if f.suffix.lower() in exts]
    download_cfg = config.get("download", {})
    keywords = download_cfg.get("video_keywords", ["night city", "rain", "cinematic"])
    min_dur = download_cfg.get("video_min_duration", 5)
    max_dur = download_cfg.get("video_max_duration", 30)

    # Reuse cache with 50% probability if we have 5+ videos (avoid always downloading)
    if len(cached) >= 5 and random.random() < 0.5:
        return random.choice(cached)

    pexels_key = os.getenv("PEXELS_API_KEY", "").strip()
    pixabay_key = os.getenv("PIXABAY_API_KEY", "").strip()

    query = random.choice(keywords)
    query_encoded = quote_plus(query)

    # Try Pexels (portrait preferred for Reels)
    if pexels_key:
        videos = _pexels_search(pexels_key, query, orientation="portrait", per_page=20)
        for v in videos:
            duration = v.get("duration") or 0
            if not (min_dur <= duration <= max_dur):
                continue
            url = _pexels_best_download_url(v, prefer_portrait=True)
            if not url:
                continue
            fname = f"pexels_{v.get('id', random.randint(1, 999999))}_{_safe_filename(query)}.mp4"
            dest = cache_dir / fname
            if dest.exists():
                return dest
            if _download_file(url, dest):
                _log(f"Cached: {dest.name}")
                time.sleep(0.5)
                return dest
        # Try without duration filter
        for v in videos[:10]:
            url = _pexels_best_download_url(v, prefer_portrait=True)
            if not url:
                continue
            fname = f"pexels_{v.get('id', 0)}_{_safe_filename(query)}.mp4"
            dest = cache_dir / fname
            if _download_file(url, dest):
                _log(f"Cached: {dest.name}")
                return dest

    # Try Pixabay
    if pixabay_key:
        hits = _pixabay_search(pixabay_key, query, per_page=20)
        for h in hits:
            duration = h.get("duration") or 0
            if duration and not (min_dur <= duration <= max_dur):
                continue
            url = _pixabay_best_download_url(h)
            if not url:
                continue
            vid = h.get("videos", {})
            mid = vid.get("medium") or vid.get("large") or {}
            vid_id = h.get("id", random.randint(1, 999999))
            fname = f"pixabay_{vid_id}_{_safe_filename(query)}.mp4"
            dest = cache_dir / fname
            if dest.exists():
                return dest
            if _download_file(url, dest):
                _log(f"Cached: {dest.name}")
                return dest
        for h in hits[:10]:
            url = _pixabay_best_download_url(h)
            if not url:
                continue
            vid_id = h.get("id", 0)
            fname = f"pixabay_{vid_id}_{_safe_filename(query)}.mp4"
            dest = cache_dir / fname
            if _download_file(url, dest):
                _log(f"Cached: {dest.name}")
                return dest

    # Fallback: use from cache if any
    if cached:
        return random.choice(cached)
    raise FileNotFoundError(
        "No background video. Set PEXELS_API_KEY and/or PIXABAY_API_KEY in .env (free keys at pexels.com/api and pixabay.com/api/docs), then run again."
    )
