"""
Creates vertical Reel video (9:16) from background + text + music.
1080x1920, 6-9 seconds, slow zoom, text overlay (center/lower, white bold, fade-in).
"""
import random
from pathlib import Path

from moviepy.editor import (
    AudioFileClip,
    CompositeVideoClip,
    ImageClip,
    TextClip,
    VideoFileClip,
)
from moviepy.video.fx.resize import resize

from src.config_loader import get_project_root, load_config, get_path


def _parse_color(hex_color: str) -> str:
    """Return color name or hex for MoviePy (e.g. #FFFFFF -> white or keep hex)."""
    h = (hex_color or "#FFFFFF").strip()
    if h.startswith("#") and len(h) == 7:
        return h
    return "white"


def _get_background_path(config: dict, use_auto_download: bool = True) -> Path:
    """Get background: auto-download to cache first, else pick from assets/backgrounds."""
    root = get_project_root()
    # 1) Auto-download (Path A: SAFE mode)
    if use_auto_download:
        try:
            from src.download_video import download_background_video
            return download_background_video(config)
        except Exception:
            pass
    # 2) Manual assets
    bg_dir = root / config["paths"]["assets_backgrounds"]
    if not bg_dir.exists():
        bg_dir.mkdir(parents=True, exist_ok=True)
    exts = (".jpg", ".jpeg", ".png", ".mp4", ".mov", ".webm")
    files = [f for f in bg_dir.iterdir() if f.suffix.lower() in exts]
    if not files:
        raise FileNotFoundError(
            "No background video. Set PEXELS_API_KEY and/or PIXABAY_API_KEY in .env (free keys at pexels.com/api, pixabay.com/api/docs), or add files to assets/backgrounds/."
        )
    return random.choice(files)


def _get_music_path(config: dict, use_auto_download: bool = True) -> Path | None:
    """Get music: auto-download to cache first, else pick from assets/music."""
    if use_auto_download:
        try:
            from src.download_music import get_or_download_music_path
            return get_or_download_music_path(config)
        except Exception:
            pass
    root = get_project_root()
    music_dir = root / config["paths"]["assets_music"]
    if not music_dir.exists():
        music_dir.mkdir(parents=True, exist_ok=True)
    files = list(music_dir.glob("*.mp3"))
    if not files:
        return None
    return random.choice(files)


def _get_font_path(config: dict) -> str | None:
    """Return path to a font file if exists, else None (MoviePy uses system font)."""
    root = get_project_root()
    fonts_dir = root / config["paths"]["assets_fonts"]
    if not fonts_dir.exists():
        return None
    for ext in (".ttf", ".otf"):
        fonts = list(fonts_dir.glob(f"*{ext}"))
        if fonts:
            return str(fonts[0])
    return None


def _make_background_clip(
    bg_path: Path,
    duration: float,
    width: int,
    height: int,
    zoom_direction: str = "in",
):
    """Load image or video, resize to 1080x1920, optionally apply slow zoom (if scipy available)."""
    if bg_path.suffix.lower() in (".mp4", ".mov", ".webm"):
        clip = VideoFileClip(str(bg_path))
    else:
        clip = ImageClip(str(bg_path))
        if not hasattr(clip, "duration") or clip.duration is None:
            clip = clip.set_duration(duration)

    if clip.duration < duration:
        clip = clip.loop(duration=duration)
    clip = clip.subclipped(0, duration)

    w, h = clip.size
    target_ratio = width / height
    current_ratio = w / h
    if current_ratio > target_ratio:
        new_w = int(h * target_ratio)
        clip = clip.crop(x_center=w / 2, width=new_w)
    else:
        new_h = int(w / target_ratio)
        clip = clip.crop(y_center=h / 2, height=new_h)
    clip = resize(clip, (width, height))

    # Optional slow zoom (requires scipy)
    try:
        from moviepy.video.VideoClip import VideoClip
        import numpy as np
        from scipy.ndimage import zoom as scipy_zoom

        base_clip = clip

        def make_frame_zoomed(t):
            factor = (
                1.0 + 0.06 * (t / duration)
                if zoom_direction == "in"
                else 1.06 - 0.06 * (t / duration)
            )
            frame = base_clip.get_frame(t)
            zoomed = scipy_zoom(frame, (factor, factor, 1), order=1)
            y0 = max(0, (zoomed.shape[0] - height) // 2)
            x0 = max(0, (zoomed.shape[1] - width) // 2)
            return zoomed[y0 : y0 + height, x0 : x0 + width]

        zoomed_clip = VideoClip(make_frame_zoomed, duration=duration)
        zoomed_clip = zoomed_clip.set_fps(clip.fps)
        clip = zoomed_clip
    except Exception:
        pass

    return clip


def _make_background_clip_simple(
    bg_path: Path,
    duration: float,
    width: int,
    height: int,
) -> CompositeVideoClip:
    """Load image or video, resize to fill 1080x1920. No zoom if scipy missing."""
    if bg_path.suffix.lower() in (".mp4", ".mov", ".webm"):
        clip = VideoFileClip(str(bg_path))
    else:
        clip = ImageClip(str(bg_path))

    if clip.duration < duration:
        clip = clip.loop(duration=duration)
    clip = clip.subclipped(0, duration)

    w, h = clip.size
    target_ratio = width / height
    current_ratio = w / h
    if current_ratio > target_ratio:
        new_w = int(h * target_ratio)
        clip = clip.crop(x_center=w / 2, width=new_w)
    else:
        new_h = int(w / target_ratio)
        clip = clip.crop(y_center=h / 2, height=new_h)
    clip = resize(clip, (width, height))
    return clip


def _make_text_clip(
    text: str,
    duration: float,
    width: int,
    height: int,
    font_size: int = 72,
    font_color: str = "white",
    stroke_color: str = "black",
    stroke_width: int = 2,
    position: str = "center",
    fade_in: float = 0.8,
    font_path: str | None = None,
) -> TextClip:
    """Create text overlay: center or lower, white bold, soft shadow (stroke), fade-in."""
    # Word wrap: max ~20 chars per line for 1080 width
    words = text.split()
    lines = []
    current = []
    for w in words:
        current.append(w)
        if len(" ".join(current)) > 18:
            if len(current) > 1:
                lines.append(" ".join(current[:-1]))
                current = [current[-1]]
            else:
                lines.append(" ".join(current))
                current = []
    if current:
        lines.append(" ".join(current))
    text_for_clip = "\n".join(lines)

    font = font_path or "Arial"
    try:
        txt_clip = TextClip(
            text_for_clip,
            font_size=font_size,
            font=font,
            color=font_color,
            stroke_color=stroke_color,
            stroke_width=stroke_width,
            method="caption",
            size=(width - 120, None),
            align="center",
        )
    except Exception:
        txt_clip = TextClip(
            text_for_clip,
            font_size=font_size,
            color=font_color,
            stroke_color=stroke_color,
            stroke_width=stroke_width,
            method="caption",
            size=(width - 120, None),
            align="center",
        )

    txt_clip = txt_clip.set_duration(duration)
    if fade_in > 0:
        txt_clip = txt_clip.crossfadein(fade_in)

    # Position: center or lower_third
    if position == "lower_third":
        y_pos = int(height * 0.65)
    else:
        y_pos = (height - txt_clip.h) // 2
    x_pos = (width - txt_clip.w) // 2
    txt_clip = txt_clip.set_position((x_pos, y_pos))

    return txt_clip


def create_reel(
    sentence: str,
    output_path: Path | None = None,
    config: dict | None = None,
) -> Path:
    """
    Create one Reel: background + text + music, export to output/reels.

    Args:
        sentence: Turkish text to overlay.
        output_path: Where to save the video. If None, auto-generated in output/reels.
        config: Loaded config dict. If None, load_config() is used.

    Returns:
        Path to the created video file.
    """
    if config is None:
        config = load_config()

    root = get_project_root()
    paths = config["paths"]
    video_cfg = config["video"]
    width = video_cfg.get("width", 1080)
    height = video_cfg.get("height", 1920)
    duration_min = video_cfg.get("duration_min", 6)
    duration_max = video_cfg.get("duration_max", 9)
    duration = random.uniform(duration_min, duration_max)
    duration = round(duration, 1)

    # Background
    bg_path = _get_background_path(config)
    try:
        bg_clip = _make_background_clip(
            bg_path,
            duration,
            width,
            height,
            zoom_direction=random.choice(["in", "out"]),
        )
    except Exception:
        bg_clip = _make_background_clip_simple(bg_path, duration, width, height)

    # Text
    text_cfg = video_cfg.get("text", {})
    font_path = _get_font_path(config)
    txt_clip = _make_text_clip(
        sentence,
        duration,
        width,
        height,
        font_size=text_cfg.get("font_size", 72),
        font_color=_parse_color(text_cfg.get("font_color", "#FFFFFF")),
        stroke_color=_parse_color(text_cfg.get("stroke_color", "#000000")),
        stroke_width=text_cfg.get("stroke_width", 2),
        position=text_cfg.get("position", "center"),
        fade_in=text_cfg.get("fade_in_duration", 0.8),
        font_path=font_path,
    )

    # Compose
    final = CompositeVideoClip([bg_clip, txt_clip])
    final = final.set_duration(duration)
    final = final.set_fps(video_cfg.get("fps", 30))

    # Music
    music_path = _get_music_path(config)
    audio = None
    if music_path:
        audio = AudioFileClip(str(music_path))
        if audio.duration > duration:
            audio = audio.subclipped(0, duration)
        else:
            audio = audio.audio_loop(duration=duration)
        audio = audio.volumex(0.35)
        final = final.set_audio(audio)

    # Output path
    if output_path is None:
        out_dir = root / paths["output_reels"]
        out_dir.mkdir(parents=True, exist_ok=True)
        from datetime import datetime
        name = f"reel_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        output_path = out_dir / name

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    final.write_videofile(
        str(output_path),
        fps=video_cfg.get("fps", 30),
        codec="libx264",
        audio_codec="aac",
        threads=4,
        logger=None,
    )

    # Cleanup
    try:
        final.close()
    except Exception:
        pass
    if audio is not None:
        try:
            audio.close()
        except Exception:
            pass
    try:
        bg_clip.close()
        txt_clip.close()
    except Exception:
        pass

    return output_path
