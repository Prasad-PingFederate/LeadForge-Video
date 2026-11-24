#!/usr/bin/env python3
"""
Test Suite for LeadForge-Video Queue Mode & State Deduplication.
Tests:
1. State deduplication logic (is_asin_recently_rendered, 7-day cutoff).
2. Clean subtag preservation (append_shorts_subtag).
3. Queue item conversion to internal deal format.
4. CLI execution of --from-queue with mock queue JSON.
5. Verifies companion .txt caption creation.
6. Verifies second run skips previously rendered ASIN (state deduplication).
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from generate_deal_short import (
    append_shorts_subtag,
    load_rendered_state,
    save_rendered_state,
    is_asin_recently_rendered,
    mark_asin_rendered,
    convert_queue_item_to_deal,
    STATE_FILE,
    OUTPUT_DIR,
)

def test_subtag_appending():
    print("--- Test 1: Subtag Appending (bb-shorts) ---")
    u1 = "https://www.amazon.in/dp/B08F9G3Y8D?tag=dammaiprasad-21"
    res1 = append_shorts_subtag(u1, "B08F9G3Y8D")
    assert "ascsubtag=bb-shorts" in res1, f"Missing ascsubtag in: {res1}"
    assert "tag=dammaiprasad-21" in res1, f"Missing tag in: {res1}"

    # Replace existing ascsubtag
    u2 = "https://www.amazon.in/dp/B08F9G3Y8D?tag=dammaiprasad-21&ascsubtag=bb-grid"
    res2 = append_shorts_subtag(u2, "B08F9G3Y8D")
    assert "ascsubtag=bb-shorts" in res2, f"Failed replacement: {res2}"
    assert "ascsubtag=bb-grid" not in res2, f"Old tag still present: {res2}"
    print("✓ PASS: Subtag appending works cleanly.")


def test_state_deduplication_logic():
    print("--- Test 2: State Deduplication Logic ---")
    mock_state = {}
    test_asin = "B0TESTDEDUP"
    assert not is_asin_recently_rendered(test_asin, mock_state, days=7)

    # Mark as rendered now
    mock_state[test_asin] = {
        "rendered_at_epoch": int(time.time()),
        "rendered_at_iso": "2026-11-24T05:30:00Z",
        "title": "Test Deal"
    }
    assert is_asin_recently_rendered(test_asin, mock_state, days=7), "Recent ASIN should be skipped"

    # Test ASIN rendered 8 days ago (should NOT be skipped)
    old_asin = "B0TESTOLD"
    mock_state[old_asin] = {
        "rendered_at_epoch": int(time.time() - (8 * 86400)),
        "rendered_at_iso": "2026-11-16T05:30:00Z",
        "title": "Old Deal"
    }
    assert not is_asin_recently_rendered(old_asin, mock_state, days=7), "8-day old ASIN should NOT be skipped"
    print("✓ PASS: 7-day state deduplication logic behaves correctly.")


def test_queue_mode_execution():
    print("--- Test 3: CLI --from-queue Execution & Video/Caption Generation ---")
    mock_queue_file = BASE_DIR / "data" / "test_mock_queue.json"
    mock_queue_file.parent.mkdir(parents=True, exist_ok=True)

    # Use Pigeon Kettle which has cached image and fast synthesis
    mock_queue_data = [
        {
            "asin": "B09W2GFM7Y",
            "title": "Pigeon 1.8L Stainless Steel Electric Kettle",
            "category": "Home & Kitchen",
            "mrp": 1295,
            "live_price": 549,
            "coupon_discount": 0,
            "effective_price": 549,
            "commission_rate": 0.08,
            "expected_commission": 43.92,
            "epc_score": 75.5,
            "rating": 4.1,
            "review_count": 94200,
            "image_url": "https://m.media-amazon.com/images/I/71+AAcMxYlL._SL1500_.jpg",
            "base_affiliate_url": "https://www.amazon.in/dp/B09W2GFM7Y?tag=dammaiprasad-21",
            "video_eligible": True,
            "updated_at": "2026-11-24T05:00:00Z"
        }
    ]

    with open(mock_queue_file, "w", encoding="utf-8") as f:
        json.dump(mock_queue_data, f, indent=2)

    # Ensure clean state for B09W2GFM7Y
    state = load_rendered_state()
    if "B09W2GFM7Y" in state:
        del state["B09W2GFM7Y"]
        save_rendered_state(state)

    # Run 1: Should render the deal
    cmd = [
        sys.executable,
        str(BASE_DIR / "generate_deal_short.py"),
        "--from-queue", str(mock_queue_file),
        "--max-deals", "1"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    print("Run 1 stdout:\n", res.stdout)
    if res.stderr:
        print("Run 1 stderr:\n", res.stderr)
    assert res.returncode == 0, f"Run 1 failed with exit code {res.returncode}"
    assert "Rendered 1 new deal short(s)" in res.stdout

    # Verify video was generated
    video_path = OUTPUT_DIR / "bharatbazaro_B09W2GFM7Y_hi.mp4"
    assert video_path.exists(), f"Video file {video_path} was not generated!"
    assert video_path.stat().st_size > 500000, f"Video file too small: {video_path.stat().st_size} bytes"

    # Verify companion .txt caption
    caption_path = video_path.with_suffix(".txt")
    assert caption_path.exists(), f"Caption file {caption_path} not found!"
    with open(caption_path, "r", encoding="utf-8") as f:
        caption_content = f.read()

    assert "LOOT DEAL ALERT" in caption_content
    assert "₹549" in caption_content
    assert "ascsubtag=bb-shorts" in caption_content
    assert "@Flash_Deals_Flipkart_Amazon" in caption_content
    assert "bharatbazaro.com" in caption_content
    print("✓ PASS: MP4 video and companion .txt caption generated successfully.")

    # Verify state was persisted
    state_after = load_rendered_state()
    assert "B09W2GFM7Y" in state_after, "ASIN not recorded in rendered_asins.json"
    print("✓ PASS: ASIN recorded in rendered_asins.json.")

    # Run 2: Immediately re-running should SKIP the deal because it's rendered!
    print("--- Test 4: Deduplication Verification (Run 2) ---")
    res2 = subprocess.run(cmd, capture_output=True, text=True)
    print("Run 2 stdout:\n", res2.stdout)
    assert res2.returncode == 0, f"Run 2 failed with exit code {res2.returncode}"
    assert "Skipping B09W2GFM7Y (already rendered in the last 7 days)" in res2.stdout
    assert "Rendered 0 new deal short(s)" in res2.stdout
    print("✓ PASS: State deduplication successfully skipped previously rendered ASIN!")


def test_deliver_short_dry_run():
    print("--- Test 5: deliver_short.py Dry-run ---")
    cmd = [sys.executable, str(BASE_DIR / "deliver_short.py")]
    res = subprocess.run(cmd, capture_output=True, text=True)
    combined = res.stdout + res.stderr
    assert res.returncode == 0, f"deliver_short failed with code {res.returncode}: {combined}"
    assert "Skipping staging delivery" in combined or "Delivery complete" in combined
    print("✓ PASS: deliver_short.py dry-run completed cleanly without errors.")


if __name__ == "__main__":
    test_subtag_appending()
    test_state_deduplication_logic()
    test_queue_mode_execution()
    test_deliver_short_dry_run()
    print("\n=========================================")
    print("ALL TESTS PASSED WITH 100% SUCCESS!")
    print("=========================================")
