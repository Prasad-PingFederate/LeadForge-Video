"""Unit tests for Google Drive archiving and Telegram Drive link integration."""

from __future__ import annotations

import json
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def _ensure_google_stubs() -> None:
    """Provide lightweight stubs if google-api-python-client is not installed locally."""
    if "googleapiclient.discovery" in sys.modules:
        return
    try:
        import googleapiclient.discovery  # noqa: F401
        import googleapiclient.http  # noqa: F401
        import google.oauth2.credentials  # noqa: F401
        import google.auth.transport.requests  # noqa: F401
        return
    except ImportError:
        pass

    google_mod = sys.modules.setdefault("google", types.ModuleType("google"))
    auth_mod = sys.modules.setdefault("google.auth", types.ModuleType("google.auth"))
    transport_mod = sys.modules.setdefault(
        "google.auth.transport", types.ModuleType("google.auth.transport")
    )
    requests_mod = sys.modules.setdefault(
        "google.auth.transport.requests", types.ModuleType("google.auth.transport.requests")
    )
    requests_mod.Request = MagicMock()
    oauth2_mod = sys.modules.setdefault("google.oauth2", types.ModuleType("google.oauth2"))
    creds_mod = sys.modules.setdefault(
        "google.oauth2.credentials", types.ModuleType("google.oauth2.credentials")
    )
    creds_mod.Credentials = MagicMock()

    gapi_mod = sys.modules.setdefault("googleapiclient", types.ModuleType("googleapiclient"))
    disc_mod = sys.modules.setdefault(
        "googleapiclient.discovery", types.ModuleType("googleapiclient.discovery")
    )
    disc_mod.build = MagicMock()
    http_mod = sys.modules.setdefault(
        "googleapiclient.http", types.ModuleType("googleapiclient.http")
    )
    http_mod.MediaFileUpload = MagicMock()

    google_mod.auth = auth_mod
    google_mod.oauth2 = oauth2_mod
    auth_mod.transport = transport_mod
    transport_mod.requests = requests_mod
    oauth2_mod.credentials = creds_mod
    gapi_mod.discovery = disc_mod
    gapi_mod.http = http_mod


_ensure_google_stubs()

import deliver_short  # noqa: E402
import upload_to_gdrive  # noqa: E402


def _make_mock_service():
    service = MagicMock()
    files_api = service.files.return_value
    return service, files_api


def test_missing_env_vars_graceful_skip(monkeypatch, tmp_path, capsys):
    for key in upload_to_gdrive.REQUIRED_ENV_VARS:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(upload_to_gdrive, "OUTPUT_DIR", tmp_path)

    rc = upload_to_gdrive.main()
    assert rc == 0
    captured = capsys.readouterr()
    assert "Skipping Google Drive upload; missing env vars" in captured.out


def test_get_or_create_folder_creates_when_missing():
    service, files_api = _make_mock_service()
    files_api.list.return_value.execute.return_value = {"files": []}
    files_api.create.return_value.execute.return_value = {"id": "folder_new_123"}

    folder_id = upload_to_gdrive.get_or_create_folder(service, "2026-11-25", "root_folder_1")
    assert folder_id == "folder_new_123"
    files_api.create.assert_called_once()


def test_get_or_create_folder_reuses_existing():
    service, files_api = _make_mock_service()
    files_api.list.return_value.execute.return_value = {"files": [{"id": "folder_existing_99"}]}

    folder_id = upload_to_gdrive.get_or_create_folder(service, "2026-11-25", "root_folder_1")
    assert folder_id == "folder_existing_99"
    files_api.create.assert_not_called()


def test_upload_file_deduplicates_existing(tmp_path):
    service, files_api = _make_mock_service()
    video = tmp_path / "bharatbazaro_B0TEST123_hi.mp4"
    video.write_bytes(b"mp4")

    files_api.list.return_value.execute.return_value = {
        "files": [
            {
                "id": "existing_id_1",
                "name": video.name,
                "webViewLink": "https://drive.google.com/file/d/existing_id_1/view",
            }
        ]
    }

    res = upload_to_gdrive.upload_file(service, video, "folder_1", "video/mp4")
    assert res["id"] == "existing_id_1"
    files_api.create.assert_not_called()


def test_main_uploads_final_videos_skips_intermediates_and_writes_manifest(monkeypatch, tmp_path):
    for key in upload_to_gdrive.REQUIRED_ENV_VARS:
        monkeypatch.setenv(key, f"val_{key}")
    monkeypatch.setattr(upload_to_gdrive, "OUTPUT_DIR", tmp_path)

    # Intermediates that must be ignored
    (tmp_path / "B0TEST123_clip_0.mp4").write_bytes(b"clip")
    (tmp_path / "B0TEST123_visual.mp4").write_bytes(b"visual")
    # Final rendered video + caption
    final_mp4 = tmp_path / "bharatbazaro_B0TEST123_hi.mp4"
    final_mp4.write_bytes(b"final")
    final_txt = tmp_path / "bharatbazaro_B0TEST123_hi.txt"
    final_txt.write_text("Deal caption", encoding="utf-8")

    service, files_api = _make_mock_service()
    # 1st list: date folder missing -> create; 2nd list: mp4 missing -> create; 3rd list: txt missing -> create
    files_api.list.return_value.execute.side_effect = [
        {"files": []},
        {"files": []},
        {"files": []},
    ]
    files_api.create.return_value.execute.side_effect = [
        {"id": "date_folder_1"},
        {
            "id": "vid_id_1",
            "name": final_mp4.name,
            "webViewLink": "https://drive.google.com/file/d/vid_id_1/view",
        },
        {
            "id": "cap_id_1",
            "name": final_txt.name,
            "webViewLink": "https://drive.google.com/file/d/cap_id_1/view",
        },
    ]

    with patch.object(upload_to_gdrive, "get_drive_service", return_value=service):
        rc = upload_to_gdrive.main()

    assert rc == 0
    manifest_path = tmp_path / "gdrive_manifest.json"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert len(manifest) == 1
    assert manifest[0]["filename"] == final_mp4.name
    assert manifest[0]["file_id"] == "vid_id_1"
    assert manifest[0]["caption_file_id"] == "cap_id_1"
    assert manifest[0]["web_view_link"] == "https://drive.google.com/file/d/vid_id_1/view"


def test_deliver_short_appends_gdrive_link(tmp_path):
    manifest = [
        {
            "filename": "bharatbazaro_B0TEST123_hi.mp4",
            "file_id": "vid_id_1",
            "web_view_link": "https://drive.google.com/file/d/vid_id_1/view",
        }
    ]
    (tmp_path / "gdrive_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    links = deliver_short.load_gdrive_links(tmp_path)
    assert links["bharatbazaro_B0TEST123_hi.mp4"] == "https://drive.google.com/file/d/vid_id_1/view"

    vid = tmp_path / "bharatbazaro_B0TEST123_hi.mp4"
    vid.write_bytes(b"mp4")
    cap = tmp_path / "bharatbazaro_B0TEST123_hi.txt"
    cap.write_text("Great deal!", encoding="utf-8")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    with patch("deliver_short.requests.post", return_value=mock_resp) as mock_post:
        ok = deliver_short.deliver_video_to_telegram(
            vid,
            cap,
            "bot-token",
            "chat-1",
            drive_link=links[vid.name],
        )

    assert ok is True
    sent_caption = mock_post.call_args.kwargs["data"]["caption"]
    assert "Great deal!" in sent_caption
    assert "Drive Archive: https://drive.google.com/file/d/vid_id_1/view" in sent_caption


def test_select_queue_deals_fallback_and_force():
    import time
    import generate_deal_short

    now = int(time.time())
    state = {
        "Q1": {"rendered_at_epoch": now - 3600},
        "Q2": {"rendered_at_epoch": now - 3600},
        "F_RENDERED": {"rendered_at_epoch": now - 3600},
    }
    queue_items = [
        {"asin": "Q1", "title": "Queue 1", "epc_score": 500},
        {"asin": "Q2", "title": "Queue 2", "epc_score": 400},
        {"asin": "Q3", "title": "Queue 3", "epc_score": 300},
    ]
    feed_items = [
        {"asin": "F_INELIGIBLE", "video_eligible": False, "epc_score": 999},
        {"asin": "F_LOW", "video_eligible": True, "epc_score": 50},
        {"asin": "F_RENDERED", "video_eligible": True, "epc_score": 800},
        {"asin": "F_HIGH", "video_eligible": True, "epc_score": 250},
        {"asin": "F_MID", "video_eligible": True, "epc_score": 150},
    ]

    picked = generate_deal_short.select_queue_deals(
        queue_items, feed_items, state, max_deals=3, force=False, days=7
    )
    assert [d["asin"] for d in picked] == ["Q3", "F_HIGH", "F_MID"]

    forced = generate_deal_short.select_queue_deals(
        queue_items, feed_items, state, max_deals=3, force=True, days=7
    )
    assert [d["asin"] for d in forced] == ["Q1", "Q2", "Q3"]
