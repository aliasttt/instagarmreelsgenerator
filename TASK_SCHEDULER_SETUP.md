# Fully Automatic Daily Run – Task Scheduler Setup

After setup, **you never open terminal or run scripts manually**.  
Every day the system runs automatically and produces one Reel + caption.  
You only open the output folder and take the ready video.

---

## One-Time Setup (Do Once)

### 1. Install Python

- Install Python 3.10+ from [python.org](https://www.python.org/downloads/).
- During install, check **"Add Python to PATH"**.

### 2. Install Dependencies (One Time Only)

Open **Command Prompt** or **PowerShell** once, go to the project folder, and run:

```powershell
cd "C:\Users\...\Desktop\InstaGenerate"
pip install -r requirements.txt
```

(Or use a virtualenv: `python -m venv .venv`, then `.venv\Scripts\activate`, then `pip install -r requirements.txt`.)

### 3. Set API Keys (One Time Only)

1. Copy `.env.example` to `.env` in the project folder.
2. Edit `.env` and set:
   - `PEXELS_API_KEY=` (get free key: https://www.pexels.com/api/)
   - `PIXABAY_API_KEY=` (get free key: https://pixabay.com/api/docs/)

Save the file.

### 4. Register the Daily Task (One Time Only)

1. Open **File Explorer** and go to the project folder `InstaGenerate`.
2. Open the `scripts` folder.
3. **Right-click** `setup_task_scheduler.ps1` → **Run with PowerShell**.
4. If Windows asks “Do you want to allow this script to run?”, choose **Yes** or **Run anyway**.
5. You should see: *Task 'InstaGenerate' registered...*

If you get an error about execution policy, open PowerShell **as Administrator** and run once:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then run the script again (right-click → Run with PowerShell).

---

## After Setup – No More Manual Steps

- **Do not** open terminal.
- **Do not** run `python` or any script manually.
- **Do not** run `run_daily.bat` by hand.

**Task Scheduler** will:

1. Run **every day at 22:00** (Turkey time if your PC is set to Turkey; otherwise 22:00 in your current time zone).
2. If the PC was **off** at 22:00, run **as soon as possible** after you turn it on (e.g. next day when you log in).

**Flow:**

```
Task Scheduler (22:00 or after missed start)
    → run_daily.bat
        → python run_daily.py
            → full pipeline (text, download video/music, create reel, caption, save, log)
    → exit
```

**Output (every day):**

- `output/reels/reel_YYYY-MM-DD.mp4` – ready to upload
- `output/captions/caption_YYYY-MM-DD.txt` – caption + hashtags
- `logs/daily.log` – success or error (no UI, no prompts)

**Double-run:** If the reel for today already exists (`reel_YYYY-MM-DD.mp4`), the pipeline skips and only logs.

---

## Your Daily Action

1. Open the **output** folder:  
   `InstaGenerate\output\reels`
2. Take the latest file: **reel_YYYY-MM-DD.mp4**
3. Optionally open `output\captions\caption_YYYY-MM-DD.txt` for the caption.
4. Upload the video to Instagram when you want.

No terminal. No scripts. No commands.

---

## Optional: Change Run Time

1. Open **Task Scheduler** (search “Task Scheduler” in Windows).
2. Find task **InstaGenerate**.
3. Right-click → **Properties** → **Triggers** tab.
4. Edit the trigger and set the time you want (e.g. 21:00 or 23:00).
5. OK.

---

## Troubleshooting

- **No video in output/reels**  
  Check `logs/daily.log` for errors. Most often: missing or invalid `PEXELS_API_KEY` / `PIXABAY_API_KEY` in `.env`.

- **Task doesn’t run**  
  In Task Scheduler, right-click **InstaGenerate** → **Run**. If it runs manually, the schedule is correct; check that the PC is on and logged in at 22:00 (or that “Run task as soon as possible after a scheduled start is missed” is enabled).

- **Wrong time zone**  
  Set Windows to **Turkey (Istanbul)** if you want 22:00 Turkey time. Or leave your time zone and set the task trigger to the local time you want (e.g. 22:00 your time).
