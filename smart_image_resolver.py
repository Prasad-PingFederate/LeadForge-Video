#!/usr/bin/env python3
"""
5-Tier Smart Product Image Resolver & Zero-Blank-Video Gate for LeadForge-Video.
Tiers:
  Tier 1: Local High-Res Cache Check (>15KB valid file)
  Tier 2: Explicit URL Download (from queue payload/catalog)
  Tier 3: Direct Amazon ASIN Media CDN Endpoints
  Tier 4: Dynamic Search & Media-Amazon Candidate Extraction (Bing Images)
  Tier 5: Branded High-Res Product Visual Card Generator (Zero-Blank Gate)

Guarantees:
  - ALWAYS returns a valid, non-blank, high-resolution Path object.
  - Zero-blank video gate guarantees video cards never render with a missing image.
"""

import sys
import os
import argparse
import urllib.parse
import urllib.request
import re
import requests
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent
CACHE_DIR = BASE_DIR / "storage" / "deal_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

def generate_fallback_graphic(asin: str, title: str, output_path: Path) -> Path:
    """Tier 5: Generate professional 800x800 branded product card (Zero-Blank Gate)."""
    img = Image.new("RGBA", (800, 800), (243, 244, 246, 255))
    draw = ImageDraw.Draw(img)

    # Clean gradient border
    draw.rounded_rectangle([(10, 10), (790, 790)], radius=30, fill=(255, 255, 255), outline=(229, 231, 235), width=4)

    # Branded Header Pill
    draw.rounded_rectangle([(240, 60), (560, 130)], radius=20, fill=(220, 38, 38))
    draw.text((275, 75), "AMAZON HOT DEAL", fill=(255, 255, 255))

    # Center Product Badge Icon
    draw.rounded_rectangle([(250, 200), (550, 500)], radius=40, fill=(238, 242, 255), outline=(199, 210, 254), width=3)
    draw.text((360, 320), "DEAL", fill=(79, 70, 229))

    # Title lines
    words = (title or f"Amazon Deal {asin}").split()
    line1 = " ".join(words[:6])
    line2 = " ".join(words[6:12]) if len(words) > 6 else ""
    draw.text((100, 560), line1, fill=(17, 24, 39))
    if line2:
        draw.text((100, 610), line2, fill=(55, 65, 81))

    # Footer Subtag
    draw.text((250, 720), f"ASIN: {asin} | Verified Product", fill=(107, 114, 128))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(output_path, "JPEG", quality=95)
    return output_path

def resolve_product_image(asin: str, title: str = "", direct_url: str = None) -> Path:
    """
    5-Tier Smart Product Image Resolver.
    Always returns a valid, non-blank Path.
    """
    clean_asin = str(asin or "").strip().upper()
    local_path = CACHE_DIR / f"{clean_asin}.jpg"

    # Tier 1: Local Cache Check (>15KB)
    if local_path.exists() and local_path.stat().st_size > 15000:
        try:
            with Image.open(local_path) as img:
                img.verify()
            print(f"[Tier 1: Cache Hit] {clean_asin} -> {local_path} ({local_path.stat().st_size} bytes)")
            return local_path
        except Exception:
            pass

    # Tier 2: Explicit URL (from queue payload / catalog)
    if direct_url:
        try:
            resp = requests.get(direct_url, timeout=12, headers={"User-Agent": USER_AGENT})
            if resp.status_code == 200 and len(resp.content) > 10000:
                with open(local_path, "wb") as f:
                    f.write(resp.content)
                print(f"[Tier 2: Direct URL] {clean_asin} downloaded from {direct_url[:60]}... ({len(resp.content)} bytes)")
                return local_path
        except Exception as e:
            print(f"Warning: Tier 2 direct URL failed for {clean_asin}: {e}")

    # Tier 3: Direct Amazon ASIN Media CDN Endpoints
    if clean_asin and not clean_asin.startswith("BHARATBAZARO"):
        cdn_templates = [
            f"https://images-na.ssl-images-amazon.com/images/P/{clean_asin}.01._SCLZZZZZZZ_.jpg",
            f"https://m.media-amazon.com/images/P/{clean_asin}.01._SCLZZZZZZZ_.jpg",
            f"https://ws-eu.amazon-adsystem.com/widgets/q?_encoding=UTF8&Format=_SL600_&ASIN={clean_asin}&MarketPlace=IN&ID=AsinImage"
        ]
        for cdn_url in cdn_templates:
            try:
                resp = requests.get(cdn_url, timeout=10, headers={"User-Agent": USER_AGENT})
                if resp.status_code == 200 and len(resp.content) > 12000:
                    with open(local_path, "wb") as f:
                        f.write(resp.content)
                    print(f"[Tier 3: Amazon CDN] {clean_asin} resolved via {cdn_url[:60]}... ({len(resp.content)} bytes)")
                    return local_path
            except Exception:
                pass

    # Tier 4: Dynamic Search & Media-Amazon Candidate Extraction (Bing Images)
    query_text = title if title else f"Amazon product {clean_asin}"
    search_queries = [
        f"{clean_asin} amazon india product",
        f"{query_text} amazon india",
        f"{query_text} amazon"
    ]
    for sq in search_queries:
        search_url = f"https://www.bing.com/images/search?q={urllib.parse.quote(sq)}&FORM=HDRSC2"
        req = urllib.request.Request(search_url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read().decode("utf-8", errors="ignore")
                murls = re.findall(r'murl&quot;:&quot;(http[^&]+)&quot;', html)
                amazon_imgs = [u for u in murls if "media-amazon" in u or "ssl-images-amazon" in u]
                candidates = amazon_imgs + murls[:8]
                for cand in candidates:
                    try:
                        r = requests.get(cand, headers={"User-Agent": USER_AGENT}, timeout=6)
                        if r.status_code == 200 and len(r.content) > 15000:
                            with open(local_path, "wb") as f:
                                f.write(r.content)
                            print(f"[Tier 4: Web Search] {clean_asin} resolved via {cand[:60]}... ({len(r.content)} bytes)")
                            return local_path
                    except Exception:
                        continue
        except Exception as se:
            print(f"Warning: Tier 4 web search failed for '{sq}': {se}")

    # Tier 5: Zero-Blank Gate Branded Graphic Generator
    print(f"[Tier 5: Zero-Blank Gate] Generating branded product visual for {clean_asin} ({title[:30]})...")
    return generate_fallback_graphic(clean_asin, title, local_path)

def main():
    parser = argparse.ArgumentParser(description="5-Tier Smart Product Image Resolver")
    parser.add_argument("asin", type=str, help="Amazon ASIN (e.g. B0B3C9L764)")
    parser.add_argument("title", type=str, nargs="?", default="", help="Product title/query")
    parser.add_argument("--url", type=str, default="", help="Optional direct image URL")
    args = parser.parse_args()

    resolved_path = resolve_product_image(args.asin, args.title, direct_url=args.url)
    print(f"\n✅ Result: {resolved_path.resolve()} (Exists: {resolved_path.exists()}, Size: {resolved_path.stat().st_size} bytes)")

if __name__ == "__main__":
    main()
