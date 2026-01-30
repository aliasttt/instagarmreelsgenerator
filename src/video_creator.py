"""
Creates vertical Reel video (9:16) from background + text + music.
1080x1920, 6-9 seconds, slow zoom, text overlay (center/lower, white bold, fade-in).
Text has its own backdrop (independent of video) so it stays readable with any text color.
Turkish characters (ş, ğ, ı, ç, ö, ü) supported via system font.
"""
import os
import random
from pathlib import Path

import numpy as np

try:
    from moviepy import (
        AudioFileClip,
        CompositeVideoClip,
        ImageClip,
        TextClip,
        VideoFileClip,
    )
except ImportError:
    from moviepy.editor import (
        AudioFileClip,
        CompositeVideoClip,
        ImageClip,
        TextClip,
        VideoFileClip,
    )

from src.config_loader import get_project_root, load_config, get_path


def _mp_resize(clip, size):
    """MoviePy 1.x: resize(clip, size). MoviePy 2.x: clip.resized(size)."""
    if hasattr(clip, "resized"):
        return clip.resized(size)
    return clip.resize(size)


def _mp_crop(clip, **kwargs):
    """MoviePy 1.x: clip.crop(**). MoviePy 2.x: clip.cropped(**)."""
    if hasattr(clip, "cropped"):
        return clip.cropped(**kwargs)
    return clip.crop(**kwargs)


def _mp_duration(clip, duration):
    if hasattr(clip, "with_duration"):
        return clip.with_duration(duration)
    return clip.set_duration(duration)


def _mp_fps(clip, fps):
    if hasattr(clip, "with_fps"):
        return clip.with_fps(fps)
    return clip.set_fps(fps)


def _mp_position(clip, pos):
    if hasattr(clip, "with_position"):
        return clip.with_position(pos)
    return clip.set_position(pos)


def _mp_audio(clip, audio):
    if hasattr(clip, "with_audio"):
        return clip.with_audio(audio)
    return clip.set_audio(audio)


def _get_turkish_font_path() -> str | None:
    """Return path to a font that supports Turkish (ş, ğ, ı, ç, ö, ü). Prefer Segoe UI on Windows."""
    if os.name == "nt":
        windir = os.environ.get("WINDIR", "C:\\Windows")
        for name in ("segoeui.ttf", "segoeuib.ttf", "arial.ttf", "arialbd.ttf"):
            path = Path(windir) / "Fonts" / name
            if path.exists():
                return str(path.resolve())
    return None


def _parse_color(hex_color: str) -> str:
    """Return color name or hex for MoviePy (e.g. #FFFFFF -> white or keep hex)."""
    h = (hex_color or "#FFFFFF").strip()
    if h.startswith("#") and len(h) == 7:
        return h
    return "white"


def _get_background_path(
    config: dict,
    use_auto_download: bool = True,
    content_category: str | None = None,
) -> Path:
    """Get background: auto-download (matching content mood), else pick from assets/backgrounds."""
    root = get_project_root()
    if use_auto_download:
        try:
            from src.download_video import download_background_video
            return download_background_video(config, content_category=content_category)
        except Exception:
            pass
    # 2) Manual assets
    bg_dir = root / config["paths"]["assets_backgrounds"]
    if not bg_dir.exists():
        bg_dir.mkdir(parents=True, exist_ok=True)
    exts_video = (".mp4", ".mov", ".webm")
    exts_image = (".jpg", ".jpeg", ".png")
    videos = [f for f in bg_dir.iterdir() if f.suffix.lower() in exts_video]
    images = [f for f in bg_dir.iterdir() if f.suffix.lower() in exts_image]
    files = videos if videos else images
    if not files:
        raise FileNotFoundError(
            "No background video. Set PEXELS_API_KEY and/or PIXABAY_API_KEY in .env (free keys at pexels.com/api, pixabay.com/api/docs), or add .mp4/.jpg to assets/backgrounds/."
        )
    return random.choice(files)


def _get_music_path(
    config: dict,
    use_auto_download: bool = True,
    content_category: str | None = None,
) -> Path | None:
    """Get music: auto-download (matching content mood), else pick from assets/music."""
    if use_auto_download:
        try:
            from src.download_music import get_or_download_music_path
            return get_or_download_music_path(config, content_category=content_category)
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
    """Return path to a font that supports Turkish. Prefer assets/fonts, else Windows Segoe UI/Arial."""
    root = get_project_root()
    fonts_dir = root / config["paths"]["assets_fonts"]
    if fonts_dir.exists():
        for ext in (".ttf", ".otf"):
            fonts = list(fonts_dir.glob(f"*{ext}"))
            if fonts:
                return str(fonts[0])
    return _get_turkish_font_path()


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
        clip = _mp_duration(clip, duration)

    clip_dur = getattr(clip, "duration", None) or 0
    if clip_dur and clip_dur < duration and hasattr(clip, "loop"):
        clip = clip.loop(duration=duration)
    elif clip_dur and clip_dur < duration and hasattr(clip, "with_duration"):
        clip = clip.with_duration(duration)
    clip = clip.subclipped(0, duration)

    w, h = clip.size
    target_ratio = width / height
    current_ratio = w / h
    if current_ratio > target_ratio:
        new_w = int(h * target_ratio)
        clip = _mp_crop(clip, x_center=w / 2, width=new_w)
    else:
        new_h = int(w / target_ratio)
        clip = _mp_crop(clip, y_center=h / 2, height=new_h)
    clip = _mp_resize(clip, (width, height))

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
        zoomed_clip = _mp_fps(zoomed_clip, clip.fps)
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
        clip = _mp_duration(clip, duration)

    clip_dur = getattr(clip, "duration", None) or 0
    if clip_dur and clip_dur < duration and hasattr(clip, "loop"):
        clip = clip.loop(duration=duration)
    clip = clip.subclipped(0, duration)

    w, h = clip.size
    target_ratio = width / height
    current_ratio = w / h
    if current_ratio > target_ratio:
        new_w = int(h * target_ratio)
        clip = _mp_crop(clip, x_center=w / 2, width=new_w)
    else:
        new_h = int(w / target_ratio)
        clip = _mp_crop(clip, y_center=h / 2, height=new_h)
    clip = _mp_resize(clip, (width, height))
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

    font = font_path or _get_turkish_font_path()
    try:
        kwargs = dict(
            text=text_for_clip,
            font_size=font_size,
            color=font_color,
            stroke_color=stroke_color,
            stroke_width=stroke_width,
            method="caption",
            size=(width - 120, None),
        )
        if font:
            kwargs["font"] = font
        txt_clip = TextClip(**kwargs)
    except (TypeError, OSError):
        kwargs = dict(
            text=text_for_clip,
            font_size=font_size,
            color=font_color,
            stroke_color=stroke_color,
            stroke_width=stroke_width,
            method="caption",
            size=(width - 120, None),
        )
        if font:
            kwargs["font"] = font
        txt_clip = TextClip(**kwargs)

    txt_clip = _mp_duration(txt_clip, duration)
    if fade_in > 0 and hasattr(txt_clip, "crossfadein"):
        txt_clip = txt_clip.crossfadein(fade_in)

    if position == "lower_third":
        y_pos = int(height * 0.65)
    else:
        y_pos = (height - txt_clip.h) // 2
    x_pos = (width - txt_clip.w) // 2
    txt_clip = _mp_position(txt_clip, (x_pos, y_pos))

    return txt_clip


def _make_text_backdrop_clip(
    width: int,
    height: int,
    duration: float,
    color_hex: str = "#1a1a1a",
    opacity: float = 0.85,
) -> ImageClip:
    """Create a semi-transparent dark rectangle for behind text (readable on any video)."""
    try:
        r = int(color_hex[1:3], 16) if len(color_hex) == 7 else 26
        g = int(color_hex[3:5], 16) if len(color_hex) == 7 else 26
        b = int(color_hex[5:7], 16) if len(color_hex) == 7 else 26
    except Exception:
        r, g, b = 26, 26, 26
    alpha_val = int(255 * max(0, min(1, opacity)))
    arr = np.zeros((height, width, 4), dtype=np.uint8)
    arr[:, :, 0] = r
    arr[:, :, 1] = g
    arr[:, :, 2] = b
    arr[:, :, 3] = alpha_val
    try:
        clip = ImageClip(arr, transparent=True, duration=duration)
    except TypeError:
        clip = ImageClip(arr, duration=duration)
    clip = _mp_duration(clip, duration)
    return clip


def create_reel(
    sentence: str,
    output_path: Path | None = None,
    config: dict | None = None,
    content_category: str | None = None,
) -> Path:
    """
    Create one Reel: background + text + music, export to output/reels.
    content_category: emotional/sarcastic/deep/romantic → music chosen to match (romantic, epic, etc.).
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

    # Background (Pexels/Pixabay – keywords match content mood)
    bg_path = _get_background_path(config, content_category=content_category)
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

    # Text backdrop: separate from video so text is always readable (any text color)
    txt_w = getattr(txt_clip, "w", None) or (txt_clip.size[0] if hasattr(txt_clip, "size") else width - 120)
    txt_h = getattr(txt_clip, "h", None) or (txt_clip.size[1] if hasattr(txt_clip, "size") else 120)
    pos_name = text_cfg.get("position", "center")
    x_pos = (width - txt_w) // 2
    y_pos = int(height * 0.65) if pos_name == "lower_third" else (height - txt_h) // 2

    backdrop_clip = None
    bg_cfg = text_cfg.get("text_background", {})
    if bg_cfg.get("enabled", True):
        pad_x = bg_cfg.get("padding_x", 80)
        pad_y = bg_cfg.get("padding_y", 40)
        backdrop_w = min(txt_w + pad_x, width - 40)
        backdrop_h = txt_h + pad_y
        backdrop_clip = _make_text_backdrop_clip(
            backdrop_w,
            backdrop_h,
            duration,
            color_hex=bg_cfg.get("color", "#1a1a1a"),
            opacity=bg_cfg.get("opacity", 0.85),
        )
        backdrop_x = max(0, x_pos - pad_x // 2)
        backdrop_y = max(0, y_pos - pad_y // 2)
        backdrop_clip = _mp_position(backdrop_clip, (backdrop_x, backdrop_y))

    # Compose: video -> text backdrop (if any) -> text
    layers = [bg_clip, backdrop_clip, txt_clip] if backdrop_clip is not None else [bg_clip, txt_clip]
    final = CompositeVideoClip([l for l in layers if l is not None])
    final = _mp_duration(final, duration)
    final = _mp_fps(final, video_cfg.get("fps", 30))

    # Music
    music_path = _get_music_path(config, content_category=content_category)
    audio = None
    if music_path:
        audio = AudioFileClip(str(music_path))
        if audio.duration > duration:
            audio = audio.subclipped(0, duration)
        else:
            audio = audio.audio_loop(duration=duration)
        if hasattr(audio, "volumex"):
            audio = audio.volumex(0.35)
        final = _mp_audio(final, audio)

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
        if backdrop_clip is not None:
            backdrop_clip.close()
    except Exception:
        pass

    return output_path
