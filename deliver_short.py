#!/usr/bin/env python3
"""
Deliver rendered deal shorts to private Telegram Staging Channel/Chat for 1-tap posting.
Uses TELEGRAM_BOT_TOKEN and TELEGRAM_STAGING_CHAT_ID (or ADMIN_CHAT_ID).

If credentials are not set, cleanly logs a notice and exits with 0.
"""

import os
import sys
import glob
import json
import logging
from pathlib import Path
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", stream=sys.stdout)
logger = logging.getLogger("deliver_short")

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"


def load_gdrive_links(output_dir: Path = OUTPUT_DIR) -> dict[str, str]:
    """Load filename -> web_view_link mapping from output/gdrive_manifest.json if present."""
    manifest_path = output_dir / "gdrive_manifest.json"
    if not manifest_path.exists():
        return {}
    try:
        entries = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(entries, list):
            return {}
        return {
            item["filename"]: item["web_view_link"]
            for item in entries
            if isinstance(item, dict) and item.get("filename") and item.get("web_view_link")
        }
    except Exception as e:
        logger.warning("Could not parse %s: %s", manifest_path, e)
        return {}


def deliver_video_to_telegram(
    video_path: Path,
    caption_path: Path,
    bot_token: str,
    chat_id: str,
    drive_link: str | None = None,
) -> bool:
    """Send rendered MP4 short and companion caption to private Telegram staging chat."""
    if not video_path.exists():
        logger.warning("Video file not found: %s", video_path)
        return False

    caption_text = ""
    if caption_path and caption_path.exists():
        try:
            with open(caption_path, "r", encoding="utf-8") as f:
                caption_text = f.read().strip()
        except Exception as e:
            logger.warning("Error reading caption file %s: %s", caption_path, e)

    if drive_link:
        drive_line = f"Drive Archive: {drive_link}"
        caption_text = f"{caption_text}\n\n{drive_line}" if caption_text else drive_line

    url = f"https://api.telegram.org/bot{bot_token}/sendVideo"
    # Telegram sendVideo caption limit is 1024 characters
    telegram_caption = caption_text[:1020]

    logger.info("Delivering %s to Telegram chat %s...", video_path.name, chat_id)
    try:
        with open(video_path, "rb") as video_file:
            files = {
                "video": (video_path.name, video_file, "video/mp4")
            }
            data = {
                "chat_id": chat_id,
                "caption": telegram_caption,
                "supports_streaming": True,
            }
            resp = requests.post(url, data=data, files=files, timeout=120)
            if resp.status_code == 200:
                logger.info("✓ Successfully delivered %s to Telegram staging!", video_path.name)
                # If full caption was longer than 1020 chars, send full caption in a follow-up message
                if len(caption_text) > 1020:
                    msg_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                    requests.post(msg_url, data={"chat_id": chat_id, "text": caption_text}, timeout=30)
                return True
            else:
                logger.warning("Telegram sendVideo returned HTTP %s: %s", resp.status_code, resp.text)
                return False
    except Exception as e:
        logger.warning("Exception delivering %s to Telegram: %s", video_path.name, e)
        return False


def find_final_rendered_videos(output_dir: Path) -> list[Path]:
    """Return final rendered bharatbazaro_*.mp4 files newest-first, skipping intermediates."""
    # Check exact lowercase prefix too because Windows filesystems match case-insensitively.
    candidates = (
        p for p in output_dir.glob("bharatbazaro_*.mp4")
        if p.name.startswith("bharatbazaro_")
        and "_clip_" not in p.name
        and not p.stem.endswith("_visual")
    )
    return sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)


def main():
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    staging_chat_id = (os.getenv("TELEGRAM_STAGING_CHAT_ID") or os.getenv("ADMIN_CHAT_ID") or "").strip()

    if not bot_token or not staging_chat_id:
        logger.info("TELEGRAM_BOT_TOKEN or TELEGRAM_STAGING_CHAT_ID is not set. Skipping staging delivery.")
        return 0

    # Scan output/ for final rendered mp4 files only (skip intermediate *_clip_*.mp4 / *_visual.mp4)
    mp4_files = find_final_rendered_videos(OUTPUT_DIR)
    if not mp4_files:
        logger.info("No final bharatbazaro_*.mp4 files found in %s to deliver.", OUTPUT_DIR)
        return 0

    # Deliver newest rendered MP4s from this cycle (default 2, configurable via MAX_DELIVER_SHORTS)
    max_deliver = max(1, int(os.getenv("MAX_DELIVER_SHORTS", "2")))
    drive_links = load_gdrive_links(OUTPUT_DIR)
    delivered_count = 0
    for video in mp4_files[:max_deliver]:
        caption_file = video.with_suffix(".txt")
        if not caption_file.exists():
            # Check for asin_caption.txt
            parts = video.stem.split("_")
            if len(parts) >= 2:
                alt_caption = OUTPUT_DIR / f"{parts[1]}_caption.txt"
                if alt_caption.exists():
                    caption_file = alt_caption

        success = deliver_video_to_telegram(
            video,
            caption_file,
            bot_token,
            staging_chat_id,
            drive_link=drive_links.get(video.name),
        )
        if success:
            delivered_count += 1

    logger.info("Delivery complete. Successfully sent %d short(s) to Telegram staging.", delivered_count)
    return 0


if __name__ == "__main__":
    sys.exit(main())
