"""
Auto-download background music (emotional, cinematic, sad vibe).
Uses Pixabay Music API (same key as video), then Jamendo if set, else fallback MP3 URLs.
Music matches text mood; each run prefers a new track (varied, trending).
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


# Music keywords by content mood: emotional→romantic/sad, deep→epic, sarcastic→ambient, romantic→love
MUSIC_KEYWORDS_BY_CATEGORY = {
    "emotional": ["emotional", "romantic", "sad", "melancholic", "piano"],
    "sarcastic": ["ambient", "minimal", "chill", "cold"],
    "deep": ["epic", "cinematic", "dramatic", "orchestral", "inspiring"],
    "romantic": ["romantic", "love", "emotional", "soft", "piano"],
}

# Fallback: direct MP3 URLs (royalty-free, no API key). Varied so each run can differ.
FALLBACK_MUSIC_URLS = [
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3",
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3",
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3",
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-5.mp3",
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-6.mp3",
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-7.mp3",
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-8.mp3",
]


def _pixabay_music_search(api_key: str, query: str, per_page: int = 20) -> list[dict]:
    """Search Pixabay Music API. Same key as video. Returns list of hits with audio URL."""
    if not api_key or not api_key.strip():
        return []
    url = "https://pixabay.com/api/music/"
    params = {"key": api_key.strip(), "q": query, "per_page": per_page}
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        return data.get("hits") or []
    except Exception as e:
        _log(f"Pixabay music search failed: {e}")
        return []


def _pixabay_music_audio_url(hit: dict) -> str | None:
    """Get MP3/audio URL from Pixabay music hit. Try previewURL, url, audio, etc."""
    for key in ("previewURL", "url", "audio", "preview_url", "audio_url"):
        u = hit.get(key)
        if u and isinstance(u, str) and u.strip():
            return u.strip()
    return None


def _jamendo_search(
    client_id: str,
    query: str,
    limit: int = 20,
    order: str = "popularity_week_desc",
) -> list[dict]:
    """Search Jamendo API for tracks. order=popularity_week_desc for trending-style music."""
    if not client_id or not client_id.strip():
        return []
    url = "https://api.jamendo.com/v3.0/tracks/"
    params = {
        "client_id": client_id.strip(),
        "search": query,
        "limit": limit,
        "format": "json",
        "audiodownload_allowed": "true",
        "order": order,
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


def download_background_music(
    config: dict | None = None,
    content_category: str | None = None,
    prefer_new: bool = True,
) -> Path | None:
    """
    Download one background music track to cache.
    content_category: emotional, sarcastic, deep, romantic → picks matching keywords (trendy mood).
    prefer_new: when True, try to download a new track (varied each run) instead of reusing cache.
    """
    if config is None:
        config = load_config()
    root = get_project_root()
    cache_dir = root / config["paths"]["cache_music"]
    cache_dir.mkdir(parents=True, exist_ok=True)

    download_cfg = config.get("download", {})
    if content_category and content_category in MUSIC_KEYWORDS_BY_CATEGORY:
        keywords = MUSIC_KEYWORDS_BY_CATEGORY[content_category]
    else:
        keywords = download_cfg.get("music_keywords", ["emotional", "cinematic", "sad"])

    query = random.choice(keywords)
    cached = list(cache_dir.glob("*.mp3"))
    if not prefer_new and len(cached) >= 3 and random.random() < 0.5:
        return random.choice(cached)

    # 1) Pixabay Music (same API key as video) – if endpoint exists: https://pixabay.com/api/music/
    pixabay_key = os.getenv("PIXABAY_API_KEY", "").strip()
    if pixabay_key:
        hits = _pixabay_music_search(pixabay_key, query, per_page=20)
        random.shuffle(hits)
        for hit in hits:
            url = _pixabay_music_audio_url(hit)
            if not url:
                continue
            track_id = hit.get("id") or hit.get("id_hash") or random.randint(1, 999999)
            name = _safe_filename(hit.get("title", hit.get("tags", "track")) or "track")
            fname = f"pixabay_music_{track_id}_{name}.mp3"
            dest = cache_dir / fname
            if dest.exists():
                return dest
            if _download_file(url, dest):
                _log(f"Cached: {dest.name}")
                return dest
            time.sleep(0.3)

    # 2) Jamendo (API: order by popularity_week_desc = trending/popular this week)
    client_id = os.getenv("JAMENDO_CLIENT_ID", "").strip()
    if client_id:
        order = download_cfg.get("music_order", "popularity_week_desc")
        tracks = _jamendo_search(client_id, query, limit=15, order=order)
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


def get_or_download_music_path(
    config: dict | None = None,
    content_category: str | None = None,
    prefer_new: bool = True,
) -> Path | None:
    """
    Return path to a music file. content_category matches music to text mood (emotional→romantic, deep→epic, etc.).
    prefer_new: when True (default), try to get a new/varied track each run; when False, may reuse cache.
    """
    if config is None:
        config = load_config()
    root = get_project_root()
    cache_dir = root / config["paths"]["cache_music"]
    # When we have a category, prefer downloading a new track so each reel has different music
    result = download_background_music(
        config, content_category=content_category, prefer_new=prefer_new
    )
    if result:
        return result
    cached = list(cache_dir.glob("*.mp3")) if cache_dir.exists() else []
    if cached:
        return random.choice(cached)
    return None
