"""
Auto-download background music (emotional, cinematic, sad vibe).
Uses Jamendo API if JAMENDO_CLIENT_ID is set; else fallback royalty-free MP3 URLs.
Saves to assets/cache/music.
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
    print(f"[DownloadMusic] {msg}")


# Fallback: direct MP3 URLs (royalty-free, no API key). Add more if needed.
# SoundHelix allows free use: https://www.soundhelix.com/
FALLBACK_MUSIC_URLS = [
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3",
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3",
]


def _jamendo_search(client_id: str, query: str, limit: int = 20) -> list[dict]:
    """Search Jamendo API for tracks. Returns list of track dicts."""
    if not client_id or not client_id.strip():
        return []
    url = "https://api.jamendo.com/v3.0/tracks/"
    params = {
        "client_id": client_id.strip(),
        "search": query,
        "limit": limit,
        "format": "json",
        "audiodownload_allowed": "true",
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        return data.get("results") or []
    except Exception as e:
        _log(f"Jamendo search failed: {e}")
        return []


def _jamendo_file_url(client_id: str, track_id: str) -> str:
    """Build Jamendo /tracks/file URL (API redirects to actual MP3)."""
    return f"https://api.jamendo.com/v3.0/tracks/file/?client_id={quote_plus(client_id.strip())}&id={quote_plus(track_id)}&audioformat=mp32"


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
        _log(f"Download failed: {e}")
        return False


def _safe_filename(name: str) -> str:
    return re.sub(r"[^\w\-.]", "_", name)[:80] or "music"


def download_background_music(config: dict | None = None) -> Path | None:
    """
    Download one background music track to cache.
    Tries Jamendo API first; else uses fallback royalty-free URLs.
    Returns path to MP3 file, or None if all failed (Reel can still be created without music).
    """
    if config is None:
        config = load_config()
    root = get_project_root()
    cache_dir = root / config["paths"]["cache_music"]
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Reuse cache 50% if we have 3+ files
    cached = list(cache_dir.glob("*.mp3"))
    if len(cached) >= 3 and random.random() < 0.5:
        return random.choice(cached)

    download_cfg = config.get("download", {})
    keywords = download_cfg.get("music_keywords", ["emotional", "cinematic", "sad"])

    # Jamendo (API redirects to MP3)
    client_id = os.getenv("JAMENDO_CLIENT_ID", "").strip()
    if client_id:
        query = random.choice(keywords)
        tracks = _jamendo_search(client_id, query, limit=15)
        for t in tracks:
            if not t.get("audiodownload_allowed", True):
                continue
            track_id = str(t.get("id", ""))
            if not track_id:
                continue
            url = _jamendo_file_url(client_id, track_id)
            name = _safe_filename(t.get("name", "track") or "track")
            fname = f"jamendo_{track_id}_{name}.mp3"
            dest = cache_dir / fname
            if dest.exists():
                return dest
            try:
                r = requests.get(url, stream=True, timeout=30, allow_redirects=True)
                r.raise_for_status()
                dest.parent.mkdir(parents=True, exist_ok=True)
                with open(dest, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                _log(f"Cached: {dest.name}")
                return dest
            except Exception:
                pass
            time.sleep(0.3)

    # Fallback URLs
    for url in random.sample(FALLBACK_MUSIC_URLS, min(5, len(FALLBACK_MUSIC_URLS))):
        fname = f"fallback_{hash(url) % 10**8}.mp3"
        dest = cache_dir / fname
        if dest.exists():
            return dest
        if _download_file(url, dest):
            _log(f"Cached: {dest.name}")
            return dest
        time.sleep(0.5)

    # Use existing cache if any
    if cached:
        return random.choice(cached)
    return None


def get_or_download_music_path(config: dict | None = None) -> Path | None:
    """
    Return path to a music file: use cache if available, else download one.
    """
    if config is None:
        config = load_config()
    root = get_project_root()
    cache_dir = root / config["paths"]["cache_music"]
    cached = list(cache_dir.glob("*.mp3")) if cache_dir.exists() else []
    if cached:
        return random.choice(cached)
    return download_background_music(config)
