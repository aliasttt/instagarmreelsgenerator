# InstaGenerate – Path A: SAFE Mode (Content Generation Only)

Fully automated **daily** Instagram Reels content generation with **no Instagram login or posting**.

**You never open terminal or run scripts manually.**  
After one-time setup, **Windows Task Scheduler** runs the pipeline every day.  
You only open the output folder and take the ready video.

Every day the system automatically:

1. **Generates** one viral Turkish sentence  
2. **Auto-downloads** aesthetic background videos (Pexels, Pixabay)  
3. **Auto-downloads** background music (Jamendo or fallback URLs)  
4. **Creates** a vertical Reel (1080×1920, 6–9 s) with text overlay  
5. **Generates** caption + hashtags in Turkish  
6. **Saves** `output/reels/reel_YYYY-MM-DD.mp4` and `output/captions/caption_YYYY-MM-DD.txt`  
7. **Logs** success or error to `logs/daily.log`  

**Fully automatic setup:** see **[TASK_SCHEDULER_SETUP.md](TASK_SCHEDULER_SETUP.md)** for one-time Task Scheduler setup. After that, no terminal, no manual run.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                  InstaGenerate – Path A (SAFE)                           │
├─────────────────────────────────────────────────────────────────────────┤
│  1. TEXT (src/text_generator.py + content_pools.py)                      │
│     → One Turkish viral sentence (40% emotional, 30% sarcastic,          │
│       20% deep, 10% romantic). 8–12 words, no emojis.                    │
├─────────────────────────────────────────────────────────────────────────┤
│  2. VIDEO DOWNLOAD (src/download_video.py)                                │
│     → Pexels API + Pixabay API. Keywords: night city, rain, cinematic.  │
│     → Saves to assets/cache/videos. Reuses cache.                       │
├─────────────────────────────────────────────────────────────────────────┤
│  3. MUSIC DOWNLOAD (src/download_music.py)                                │
│     → Jamendo API (optional) or fallback royalty-free URLs.              │
│     → Saves to assets/cache/music.                                       │
├─────────────────────────────────────────────────────────────────────────┤
│  4. VIDEO EDIT (src/video_creator.py)                                   │
│     → 1080×1920, 6–9 s. Background from cache (or assets/backgrounds).   │
│     → Text: white bold, fade-in, optional slow zoom. Music from cache.  │
│     → Output: output/reels/reel_YYYY-MM-DD.mp4                          │
├─────────────────────────────────────────────────────────────────────────┤
│  5. CAPTION (src/caption_generator.py)                                   │
│     → 1–2 Turkish lines + 10–15 hashtags.                               │
│     → Saved: output/captions/caption_YYYY-MM-DD.txt                     │
├─────────────────────────────────────────────────────────────────────────┤
│  6. LOG (src/logger.py) + TASK SCHEDULER                                 │
│     → logs/daily.log. Task runs daily at 22:00 (or when PC turns on).   │
└─────────────────────────────────────────────────────────────────────────┘
```

**No Instagram** – no login, no posting, no browser automation.

---

## Folder Structure

```
InstaGenerate/
├── config/config.yaml       # Paths, video, download keywords
├── src/
│   ├── config_loader.py
│   ├── content_pools.py      # Turkish sentence pools
│   ├── text_generator.py
│   ├── download_video.py     # Pexels + Pixabay
│   ├── download_music.py     # Jamendo + fallback
│   ├── video_creator.py      # MoviePy: background + text + music
│   ├── caption_generator.py
│   ├── pipeline.py           # Full pipeline (SAFE)
│   └── scheduler.py         # Daily run in window
├── assets/
│   ├── cache/
│   │   ├── videos/          # Auto-downloaded clips
│   │   └── music/           # Auto-downloaded MP3s
│   ├── backgrounds/         # Optional: manual fallback
│   ├── music/                # Optional: manual fallback
│   └── fonts/               # Optional: custom font
├── output/
│   ├── reels/               # Generated .mp4
│   └── captions/            # Generated .txt
├── logs/
├── run_daily.py             # Entry for scheduler / Task Scheduler
├── requirements.txt
└── .env                     # PEXELS_API_KEY, PIXABAY_API_KEY (optional: JAMENDO_CLIENT_ID)
```

---

## Step-by-Step Setup

### 1. Python

- Python 3.10+.
- Optional: `python -m venv .venv` then activate.

### 2. Install dependencies

```powershell
cd "C:\...\InstaGenerate"
pip install -r requirements.txt
```

(Playwright is not required for Path A.)

### 3. API keys (for auto-download)

Copy `.env.example` to `.env` and set:

- **PEXELS_API_KEY** – [Get free key](https://www.pexels.com/api/)
- **PIXABAY_API_KEY** – [Get free key](https://pixabay.com/api/docs/)

Optional:

- **JAMENDO_CLIENT_ID** – [Get free key](https://devportal.jamendo.com/) for more music variety.

Without keys, the system will fail when trying to download the first background video (you can still add files manually to `assets/backgrounds/` and `assets/music/` as fallback).

### 4. Run once (test)

```powershell
python run_daily.py --once-at-now
```

- Downloads one background video and (if possible) one music track to cache  
- Creates one Reel in `output/reels/`  
- Saves caption in `output/captions/`  
- No Instagram, no browser

### 5. Automation (Windows Task Scheduler)

**Option A – Run at login (scheduler runs daily in 21:00–23:00 Turkey)**

1. Task Scheduler → Create Basic Task  
2. Trigger: **When I log on**  
3. Action: **Start a program**  
   - Program: `python.exe` (or full path to `.venv\Scripts\python.exe`)  
   - Arguments: `"C:\...\InstaGenerate\run_daily.py"`  
   - Start in: `C:\...\InstaGenerate`  
4. Finish. Keep laptop on around 21:00–23:00 Turkey time.

**Option B – Run once per day at a fixed time**

1. Create Basic Task  
2. Trigger: **Daily**, e.g. **22:00** (adjust for Turkey timezone)  
3. Action: Start program  
   - Arguments: `"C:\...\InstaGenerate\run_daily.py" --once-at-now`  
   - Start in: `C:\...\InstaGenerate`  

---

## Usage

| Command | Description |
|--------|-------------|
| `python run_daily.py` | Start scheduler; runs pipeline once per day in 21:00–23:00 Turkey. |
| `python run_daily.py --once-at-now` | Run pipeline once now and exit. |
| `python run_daily.py --once-at-window` | Wait until next 21:00–23:00 Turkey, run once, exit. |
| `python -m src.pipeline` | Run pipeline once (same as `--once-at-now`). |

---

## Content Rules (built-in)

- **Text:** Turkish, 8–12 words, no emojis, no end punctuation. Mix: 40% emotional, 30% sarcastic, 20% deep, 10% romantic.  
- **Video:** 1080×1920, 6–9 s, text center or lower third, white bold, fade-in, optional slow zoom.  
- **Caption:** 1–2 short Turkish lines + 10–15 hashtags.  

---

## Important

- **Path A is SAFE** – no Instagram login, no posting, no browser automation.  
- **User does not add files manually** – backgrounds and music are downloaded automatically when API keys are set.  
- **Cache** – first run downloads to `assets/cache/videos` and `assets/cache/music`; later runs reuse when appropriate.  
- **Final output** – one MP4 in `output/reels/`, one TXT in `output/captions/`. Upload manually to Instagram when you want.

---

## Troubleshooting

- **“No background video”** – Set `PEXELS_API_KEY` and/or `PIXABAY_API_KEY` in `.env`. Or add at least one image/video in `assets/backgrounds/`.  
- **“Video creation failed”** – Check that FFmpeg/MoviePy can read the cached file; ensure `assets/cache/videos` has at least one .mp4.  
- **No music** – Set `JAMENDO_CLIENT_ID` for more tracks, or add .mp3 files in `assets/music/` or `assets/cache/music/`. Reels can be created without music.  
- **Wrong time** – Set `project.timezone` in `config/config.yaml` to `Europe/Istanbul` and match Windows/timezone for 21:00–23:00.
