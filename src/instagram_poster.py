"""
Post Reel to Instagram using Playwright.
Login, upload video, add caption + hashtags, post.
Uses safe delays (slow_mo) to avoid spam detection.
"""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from src.config_loader import load_config, get_instagram_credentials


def _log(msg: str) -> None:
    print(f"[Instagram] {msg}")


def post_reel(
    video_path: Path | str,
    caption: str,
    hashtags: str,
    config: dict | None = None,
) -> bool:
    """
    Post one Reel to Instagram: login, upload video, set caption + hashtags, publish.

    Args:
        video_path: Path to the .mp4 Reel file.
        caption: 1-2 line Turkish caption (no hashtags).
        hashtags: Space-separated hashtags (e.g. "#keşfet #duygular ...").
        config: Loaded config. If None, load_config() is used.

    Returns:
        True if post succeeded, False otherwise.
    """
    if config is None:
        config = load_config()

    username, password = get_instagram_credentials()
    if not username or not password:
        _log("Missing INSTAGRAM_USERNAME or INSTAGRAM_PASSWORD in .env")
        return False

    video_path = Path(video_path)
    if not video_path.exists():
        _log(f"Video not found: {video_path}")
        return False

    full_caption = caption.strip()
    if hashtags.strip():
        full_caption = full_caption + "\n\n" + hashtags.strip()

    insta_cfg = config.get("instagram", {})
    headless = insta_cfg.get("headless", False)
    slow_mo = insta_cfg.get("slow_mo", 100)
    upload_timeout_ms = (insta_cfg.get("upload_timeout", 120)) * 1000

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            viewport={"width": 412, "height": 915},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="tr-TR",
        )
        page = context.new_page()
        page.set_default_timeout(30000)

        try:
            # Login
            _log("Opening Instagram...")
            page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
            time.sleep(2)

            # Accept cookies if present
            try:
                accept = page.get_by_role("button", name="Allow essential and optional cookies").first
                if accept.is_visible():
                    accept.click()
                    time.sleep(1)
            except Exception:
                pass

            # Username
            _log("Logging in...")
            user_input = page.get_by_label("Phone number, username, or email")
            user_input.wait_for(state="visible", timeout=10000)
            user_input.fill(username, timeout=5000)
            time.sleep(slow_mo / 1000)

            # Password
            pass_input = page.get_by_label("Password")
            pass_input.fill(password, timeout=5000)
            time.sleep(slow_mo / 1000)

            # Login button
            page.get_by_role("button", name="Log in").first.click()
            time.sleep(5)

            # Save login / Not now
            try:
                not_now = page.get_by_role("button", name="Not now")
                if not_now.is_visible():
                    not_now.click()
                    time.sleep(2)
            except Exception:
                pass

            # Notifications / Not now
            try:
                not_now2 = page.get_by_role("button", name="Not Now")
                if not_now2.is_visible():
                    not_now2.click()
                    time.sleep(2)
            except Exception:
                pass

            # Create / New post
            _log("Opening create post...")
            try:
                # Plus icon or "Create" link
                create = page.locator('a[href="#"]').filter(has=page.locator("svg")).first
                create.click()
                time.sleep(2)
            except Exception:
                try:
                    page.get_by_role("link", name="New post").click()
                    time.sleep(2)
                except Exception:
                    try:
                        page.get_by_role("button", name="Create").click()
                        time.sleep(2)
                    except Exception:
                        _log("Could not find Create / New post button")
                        browser.close()
                        return False

            # Select "Reel" if there's a choice (Post / Reel / Story)
            try:
                reel_tab = page.get_by_text("Reel", exact=True).first
                if reel_tab.is_visible():
                    reel_tab.click()
                    time.sleep(1)
            except Exception:
                pass

            # File input for upload
            _log("Selecting video...")
            try:
                file_input = page.locator('input[type="file"]').first
                file_input.wait_for(state="visible", timeout=10000)
                file_input.set_input_files(str(video_path.resolve()))
            except PlaywrightTimeout:
                try:
                    file_input = page.get_by_role("textbox", name="Upload").locator("..").locator("input[type=file]")
                    file_input.set_input_files(str(video_path.resolve()))
                except Exception:
                    _log("Could not find file input for upload")
                    browser.close()
                    return False
            time.sleep(5)

            # Next (after file selected)
            try:
                next_btn = page.get_by_role("button", name="Next")
                next_btn.wait_for(state="visible", timeout=upload_timeout_ms)
                next_btn.click()
                time.sleep(3)
            except Exception:
                _log("Could not find Next after file select")
                browser.close()
                return False

            # Filter / Edit step - skip with Next if present
            try:
                next_btn2 = page.get_by_role("button", name="Next")
                if next_btn2.is_visible():
                    next_btn2.click()
                    time.sleep(2)
            except Exception:
                pass

            # Caption textarea
            _log("Adding caption...")
            try:
                caption_area = page.get_by_label("Write a caption…").or_(
                    page.locator('div[aria-label="Write a caption…"]')
                ).or_(page.get_by_placeholder("Write a caption…"))
                caption_area.wait_for(state="visible", timeout=15000)
                caption_area.fill(full_caption, timeout=5000)
                time.sleep(slow_mo / 1000 * 2)
            except Exception:
                try:
                    caption_area = page.locator('textarea[placeholder*="caption"], textarea[aria-label*="caption"]').first
                    caption_area.fill(full_caption, timeout=5000)
                except Exception:
                    _log("Could not find caption field")
                    browser.close()
                    return False

            # Share / Post button
            _log("Posting...")
            try:
                share_btn = page.get_by_role("button", name="Share").or_(
                    page.get_by_role("button", name="Post")
                ).or_(page.get_by_text("Share").first).or_(page.get_by_text("Post").first)
                share_btn.wait_for(state="visible", timeout=10000)
                share_btn.click()
            except Exception:
                _log("Could not find Share/Post button")
                browser.close()
                return False

            time.sleep(5)
            _log("Reel posted successfully")
            return True

        except Exception as e:
            _log(f"Error: {e}")
            return False
        finally:
            browser.close()


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 4:
        print("Usage: python -m src.instagram_poster <video_path> <caption> <hashtags>")
        sys.exit(1)
    ok = post_reel(sys.argv[1], sys.argv[2], sys.argv[3])
    sys.exit(0 if ok else 1)
