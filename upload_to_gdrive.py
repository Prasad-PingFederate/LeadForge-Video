#!/usr/bin/env python3
"""Upload final rendered deal shorts and captions to Google Drive via OAuth 2.0.

Uses OAuth 2.0 user credentials (not a Service Account) so uploads count
against the user's personal Google Drive storage quota.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from deliver_short import find_final_rendered_videos

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"

REQUIRED_ENV_VARS = (
    "GOOGLE_DRIVE_CLIENT_ID",
    "GOOGLE_DRIVE_CLIENT_SECRET",
    "GOOGLE_DRIVE_REFRESH_TOKEN",
    "GOOGLE_DRIVE_FOLDER_ID",
)


def _escape_query_value(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def get_drive_service():
    """Build an authenticated Google Drive v3 client from OAuth refresh credentials."""
    creds = Credentials(
        token=None,
        refresh_token=os.environ["GOOGLE_DRIVE_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GOOGLE_DRIVE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_DRIVE_CLIENT_SECRET"],
        scopes=SCOPES,
    )
    creds.refresh(Request())
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def get_or_create_folder(service: Any, name: str, parent_id: str) -> str:
    """Return existing Drive subfolder ID or create it under parent_id."""
    safe_name = _escape_query_value(name)
    safe_parent = _escape_query_value(parent_id)
    q = (
        f"name = '{safe_name}' and mimeType = 'application/vnd.google-apps.folder' "
        f"and '{safe_parent}' in parents and trashed = false"
    )
    res = service.files().list(q=q, fields="files(id)").execute()
    files = res.get("files", [])
    if files:
        return files[0]["id"]

    created = (
        service.files()
        .create(
            body={
                "name": name,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [parent_id],
            },
            fields="id",
        )
        .execute()
    )
    return created["id"]


def find_existing_file(service: Any, name: str, parent_id: str) -> Optional[Dict[str, Any]]:
    """Find an existing non-trashed file by exact name inside parent_id."""
    safe_name = _escape_query_value(name)
    safe_parent = _escape_query_value(parent_id)
    q = f"name = '{safe_name}' and '{safe_parent}' in parents and trashed = false"
    res = service.files().list(q=q, fields="files(id, name, webViewLink)").execute()
    files = res.get("files", [])
    return files[0] if files else None


def upload_file(service: Any, path: Path, parent_id: str, mime_type: str) -> Dict[str, Any]:
    """Upload a file via resumable upload, skipping if it already exists in parent_id."""
    existing = find_existing_file(service, path.name, parent_id)
    if existing:
        print(f"Skipping existing Drive file: {path.name}")
        return existing

    media = MediaFileUpload(
        str(path),
        mimetype=mime_type,
        resumable=True,
        chunksize=5 * 1024 * 1024,
    )
    created = (
        service.files()
        .create(
            body={"name": path.name, "parents": [parent_id]},
            media_body=media,
            fields="id, name, webViewLink",
        )
        .execute()
    )
    print(f"Uploaded {path.name} -> {created.get('webViewLink')}")
    return created


def _resolve_caption_path(video_path: Path, output_dir: Path) -> Optional[Path]:
    direct = video_path.with_suffix(".txt")
    if direct.exists():
        return direct
    parts = video_path.stem.split("_")
    if len(parts) >= 2:
        alt = output_dir / f"{parts[1]}_caption.txt"
        if alt.exists():
            return alt
    return None


def main() -> int:
    missing = [k for k in REQUIRED_ENV_VARS if not os.environ.get(k)]
    if missing:
        print(f"Skipping Google Drive upload; missing env vars: {', '.join(missing)}")
        return 0

    videos = find_final_rendered_videos(OUTPUT_DIR)
    if not videos:
        print("No final rendered videos found in output/.")
        return 0

    service = get_drive_service()
    date_folder = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    target_folder_id = get_or_create_folder(
        service, date_folder, os.environ["GOOGLE_DRIVE_FOLDER_ID"]
    )

    manifest = []
    for video_path in videos:
        video_path = Path(video_path)
        uploaded = upload_file(service, video_path, target_folder_id, "video/mp4")
        entry: Dict[str, Any] = {
            "filename": video_path.name,
            "file_id": uploaded["id"],
            "web_view_link": uploaded.get("webViewLink"),
        }
        caption_path = _resolve_caption_path(video_path, OUTPUT_DIR)
        if caption_path is not None:
            cap_uploaded = upload_file(service, caption_path, target_folder_id, "text/plain")
            entry["caption_file_id"] = cap_uploaded["id"]
        manifest.append(entry)

    manifest_path = OUTPUT_DIR / "gdrive_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Saved Drive manifest to {manifest_path} ({len(manifest)} videos).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
