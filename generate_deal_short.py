"""
BharatBazaro Deal Short Generator (LeadForge-Video)
Generates high-converting 9:16 vertical videos (YouTube Shorts / Instagram Reels / WhatsApp Status)
for Amazon deals with ZERO external paid models and ZERO API costs.

Voice: Microsoft Edge TTS (100% Free, unlimited, natural Indian voices)
Video Engine: Local FFmpeg (Bundled via imageio-ffmpeg)
Visuals: Dynamic 1080x1920 PIL slides with Amazon deal imagery, themed colors & price badges
"""

import os
import sys
import argparse
import asyncio
import subprocess
import requests
import json
import urllib.request
import urllib.parse
import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Set up paths
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
CACHE_DIR = BASE_DIR / "storage" / "deal_cache"
CACHE_DIR.mkdir(exist_ok=True, parents=True)

# FFmpeg binary detection
FFMPEG_EXE = r"C:\Users\prasad.dammai\AppData\Roaming\Python\Python315\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
if not Path(FFMPEG_EXE).exists():
    try:
        import imageio_ffmpeg
        FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        FFMPEG_EXE = "ffmpeg"

# Curated High-Converting Deals with 100% Verified Amazon Images, Themes, Voices & Music
SAMPLE_DEALS = [
    {
        "asin": "B09W2GFM7Y",
        "title": "Pigeon 1.8 Litre Stainless Steel Electric Kettle",
        "category": "Hostel & Daily Essentials",
        "mrp": 1295,
        "price": 549,
        "discount": 58,
        "savings": 746,
        "rating": 4.1,
        "reviews": 94200,
        "image_url": "https://m.media-amazon.com/images/I/71+AAcMxYlL._SL1500_.jpg",
        "affiliate_url": "https://www.amazon.in/dp/B09W2GFM7Y?tag=dammaiprasad-21",
        "default_lang": "hi",
        "default_voice": "hi-IN-SwaraNeural",
        "theme": {
            "bg_color": (30, 27, 75),           # Deep Indigo
            "header_color": (234, 88, 12),      # Flame Orange
            "header_text": "🔥 HOSTEL & HOME MUST-HAVE 🔥",
            "price_box_color": (49, 46, 129),
            "accent_color": (251, 191, 36),
            "badge_color": (220, 38, 38),
            "bgm": "output003.mp3",
            "hook_badge": "⚡ 94,000+ REVIEWS"
        }
    },
    {
        "asin": "B08F9G3Y8D",
        "title": "Philips All-in-One Multi Grooming Kit 9-in-1",
        "category": "Men's Grooming",
        "mrp": 2295,
        "price": 1449,
        "discount": 37,
        "savings": 846,
        "rating": 4.4,
        "reviews": 51200,
        "image_url": "https://m.media-amazon.com/images/I/710+Q7e0H4L._SL1500_.jpg",
        "affiliate_url": "https://www.amazon.in/dp/B08F9G3Y8D?tag=dammaiprasad-21",
        "default_lang": "en",
        "default_voice": "en-IN-NeerjaNeural",
        "theme": {
            "bg_color": (24, 24, 27),           # Obsidian Black
            "header_color": (37, 99, 235),      # Philips Royal Blue
            "header_text": "✨ PHILIPS SALON PRECISION ✨",
            "price_box_color": (39, 39, 42),
            "accent_color": (96, 165, 250),
            "badge_color": (217, 119, 6),
            "bgm": "output006.mp3",
            "hook_badge": "⭐ 9-IN-1 TRIMMER"
        }
    },
    {
        "asin": "B09VDN3T3D",
        "title": "Portronics Power Bank 10000mAh 22.5W Fast Charging",
        "category": "Mobile Tech & Power",
        "mrp": 1999,
        "price": 799,
        "discount": 60,
        "savings": 1200,
        "rating": 4.3,
        "reviews": 18900,
        "image_url": "https://m.media-amazon.com/images/I/61SRdzgwPTL._SL1500_.jpg",
        "affiliate_url": "https://www.amazon.in/dp/B09VDN3T3D?tag=dammaiprasad-21",
        "default_lang": "hi",
        "default_voice": "hi-IN-SwaraNeural",
        "theme": {
            "bg_color": (88, 28, 135),          # Royal Violet
            "header_color": (219, 39, 119),     # Pink / Magenta
            "header_text": "🔋 POCKET POWER BANK LOOT 🔋",
            "price_box_color": (107, 33, 168),
            "accent_color": (244, 114, 182),
            "badge_color": (245, 158, 11),
            "bgm": "output007.mp3",
            "hook_badge": "⚡ 22.5W FAST CHARGE"
        }
    },
    {
        "asin": "B091CR2FXY",
        "title": "AGARO Regency Air Fryer 12L 1800W",
        "category": "Appliances & Cooking",
        "mrp": 15999,
        "price": 7499,
        "discount": 53,
        "savings": 8500,
        "rating": 4.5,
        "reviews": 12800,
        "image_url": "https://m.media-amazon.com/images/I/71I4jRRRCmL._SL1500_.jpg",
        "affiliate_url": "https://www.amazon.in/dp/B091CR2FXY?tag=dammaiprasad-21",
        "default_lang": "en",
        "default_voice": "en-IN-PrabhatNeural",
        "theme": {
            "bg_color": (6, 78, 59),            # Emerald Forest
            "header_color": (16, 185, 129),     # Emerald Green
            "header_text": "⚡ 53% OFF MASSIVE PRICE DROP ⚡",
            "price_box_color": (4, 47, 46),
            "accent_color": (52, 211, 153),
            "badge_color": (217, 119, 6),
            "bgm": "output002.mp3",
            "hook_badge": "🏆 SAVE FLAT ₹8,500"
        }
    },
    {
        "asin": "B002MPPTB8",
        "title": "Hawkins Futura Hard Anodised Pressure Cooker 3L",
        "category": "Home & Kitchen",
        "mrp": 3350,
        "price": 2499,
        "discount": 25,
        "savings": 851,
        "rating": 4.4,
        "reviews": 28400,
        "image_url": "https://m.media-amazon.com/images/I/51ENhZPIl2L._SL1500_.jpg",
        "affiliate_url": "https://www.amazon.in/dp/B002MPPTB8?tag=dammaiprasad-21",
        "default_lang": "hi",
        "default_voice": "hi-IN-MadhurNeural",
        "theme": {
            "bg_color": (15, 23, 42),           # Slate Navy
            "header_color": (220, 38, 38),       # Kitchen Crimson
            "header_text": "💥 BHARATBAZARO KITCHEN LOOT 💥",
            "price_box_color": (30, 41, 59),
            "accent_color": (245, 158, 11),      # Amber
            "badge_color": (234, 88, 12),
            "bgm": "output001.mp3",
            "hook_badge": "🔥 TOP RATED COOKER"
        }
    },
    {
        "asin": "B09NVPSCQT",
        "title": "Noise Buds VS102 Wireless Earbuds 50H Playtime",
        "category": "Electronics & Audio",
        "mrp": 2999,
        "price": 899,
        "discount": 70,
        "savings": 2100,
        "rating": 4.2,
        "reviews": 68400,
        "image_url": "https://m.media-amazon.com/images/I/61wemCOc3vL._SL1500_.jpg",
        "affiliate_url": "https://www.amazon.in/dp/B09NVPSCQT?tag=dammaiprasad-21",
        "default_lang": "en",
        "default_voice": "en-IN-PrabhatNeural",
        "theme": {
            "bg_color": (15, 23, 42),           # Cyber Slate
            "header_color": (124, 58, 237),     # Electric Purple
            "header_text": "🎧 UNDER ₹999 TECH LOOT 🎧",
            "price_box_color": (24, 24, 27),
            "accent_color": (6, 182, 212),      # Cyan
            "badge_color": (147, 51, 234),
            "bgm": "output004.mp3",
            "hook_badge": "⚡ 50H BATTERY LIFE"
        }
    },
    {
        "asin": "B0BY2W1H1S",
        "title": "Fastrack Limitless FS1 1.95 Display Smartwatch",
        "category": "Smartwatches & Wearables",
        "mrp": 3995,
        "price": 1299,
        "discount": 67,
        "savings": 2696,
        "rating": 4.1,
        "reviews": 34100,
        "image_url": "https://m.media-amazon.com/images/I/71BMeCVMZOL._SL1500_.jpg",
        "affiliate_url": "https://www.amazon.in/dp/B0BY2W1H1S?tag=dammaiprasad-21",
        "default_lang": "hi",
        "default_voice": "hi-IN-MadhurNeural",
        "theme": {
            "bg_color": (19, 78, 74),           # Deep Teal
            "header_color": (13, 148, 136),     # Teal
            "header_text": "⌚ SMARTWATCH CRASH DEAL ⌚",
            "price_box_color": (17, 94, 89),
            "accent_color": (45, 212, 191),
            "badge_color": (225, 29, 72),       # Rose
            "bgm": "output005.mp3",
            "hook_badge": "🔥 67% FLAT DISCOUNT"
        }
    },
    {
        "asin": "BHARATBAZARO_RADAR",
        "title": "BharatBazaro 24/7 AI Deal Radar for Amazon India",
        "category": "AI Deals & Cashback",
        "mrp": 9999,
        "price": 0,
        "discount": 100,
        "savings": 9999,
        "rating": 4.9,
        "reviews": 15000,
        "image_url": None,  # Dynamically generated 3D Radar Graphic
        "affiliate_url": "https://bharatbazaro.com",
        "default_lang": "en",
        "default_voice": "en-IN-NeerjaNeural",
        "theme": {
            "bg_color": (2, 6, 23),             # Deep Cyber Void
            "header_color": (14, 165, 233),     # Cyber Blue
            "header_text": "🤖 BHARATBAZARO AI RADAR 🤖",
            "price_box_color": (15, 23, 42),
            "accent_color": (52, 211, 153),     # Emerald
            "badge_color": (16, 185, 129),
            "bgm": "output010.mp3",
            "hook_badge": "🚀 100% FREE AI ACCESS"
        },
        "custom_script": (
            "Stop scrolling and stop overpaying on Amazon India! "
            "Meet BharatBazaro — India's 24/7 AI Deal Radar. "
            "Our automated radar tracks thousands of Amazon products every few minutes, detecting real price crashes, "
            "hidden 50% checkbox coupons, and rare lightning deals before they expire. "
            "Every single deal is Keepa-verified — zero fake discounts, only genuine historic lows. "
            "Whether you're shopping for earbuds, smartwatches, pressure cookers, or air fryers, "
            "BharatBazaro surfaces the biggest savings first. "
            "Visit bharatbazaro.com or tap the link in our bio to join our VIP channel for instant alerts. "
            "Shop smarter, save bigger!"
        )
    }
]

def get_font(size: int, bold: bool = False):
    """Resolve high quality Windows system fonts or bundled fonts."""
    font_candidates = [
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
        str(BASE_DIR / "resource" / "fonts" / "BeVietnamPro-Bold.ttf") if bold else str(BASE_DIR / "resource" / "fonts" / "BeVietnamPro-Medium.ttf"),
    ]
    for path in font_candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()

def generate_radar_graphic(output_path: Path):
    """Generate high-tech 3D Radar graphic for BharatBazaro promo."""
    w, h = 800, 760
    img = Image.new("RGBA", (w, h), (15, 23, 42, 255))
    draw = ImageDraw.Draw(img)

    center_x, center_y = w // 2, h // 2
    for r in [80, 160, 240, 320]:
        draw.ellipse([center_x - r, center_y - r, center_x + r, center_y + r], outline=(30, 58, 138), width=3)
    
    draw.line([center_x - 340, center_y, center_x + 340, center_y], fill=(30, 58, 138), width=2)
    draw.line([center_x, center_y - 340, center_x, center_y + 340], fill=(30, 58, 138), width=2)

    blips = [(center_x + 120, center_y - 80), (center_x - 140, center_y + 110), (center_x + 60, center_y + 180)]
    for bx, by in blips:
        draw.ellipse([bx - 14, by - 14, bx + 14, by + 14], fill=(16, 185, 129, 100))
        draw.ellipse([bx - 7, by - 7, bx + 7, by + 7], fill=(52, 211, 153, 255))

    draw.ellipse([center_x - 70, center_y - 70, center_x + 70, center_y + 70], fill=(14, 165, 233), outline=(255, 255, 255), width=4)
    draw.text((center_x - 30, center_y - 35), "AI", fill=(255, 255, 255), font=get_font(52, bold=True))

    draw.rounded_rectangle([100, h - 90, w - 100, h - 30], radius=15, fill=(16, 185, 129))
    draw.text((130, h - 75), "🟢 RADAR ACTIVE: SCANNING AMAZON INDIA", fill=(255, 255, 255), font=get_font(24, bold=True))

    img.save(output_path, "PNG")
    return output_path

def download_product_image(url: str, asin: str, deal_title: str) -> Path:
    """Download Amazon product image or return cached image."""
    local_path = CACHE_DIR / f"{asin}.jpg"
    
    if asin == "BHARATBAZARO_RADAR":
        radar_path = CACHE_DIR / "radar_graphic.png"
        if not radar_path.exists():
            generate_radar_graphic(radar_path)
        return radar_path

    # Check if a genuine image exists in cache (>20KB)
    if local_path.exists() and local_path.stat().st_size > 20000:
        return local_path
    
    # Download directly from URL if provided
    if url:
        try:
            resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            if resp.status_code == 200 and len(resp.content) > 15000:
                with open(local_path, "wb") as f:
                    f.write(resp.content)
                return local_path
        except Exception as e:
            print(f"Warning: Failed to download from {url}: {e}")
    
    return local_path

def create_slide_image(deal: dict, slide_idx: int) -> Path:
    """
    Generate professional 1080x1920 (9:16 vertical) deal visual card.
    Uses unique colors, badges, and layout tailored to each specific product theme.
    """
    width, height = 1080, 1920
    theme = deal.get("theme", {})
    bg_color = theme.get("bg_color", (11, 15, 25))
    header_color = theme.get("header_color", (220, 38, 38))
    accent_color = theme.get("accent_color", (52, 211, 153))
    price_box_color = theme.get("price_box_color", (24, 32, 47))
    badge_color = theme.get("badge_color", (234, 88, 12))

    img = Image.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # 1. Top Header Pill
    draw.rounded_rectangle([(80, 80), (1000, 180)], radius=30, fill=header_color)
    if slide_idx == 0:
        header_text = theme.get("header_text", "💥 BHARATBAZARO LOOT RADAR 💥")
    elif slide_idx == 1:
        header_text = "⭐ KEEP-A VERIFIED LOWEST PRICE ⭐"
    else:
        header_text = "⚡ HURRY - LIMITED TIME ONLY ⚡"
    
    h_font = get_font(36, bold=True)
    draw.text((110, 108), header_text, fill=(255, 255, 255), font=h_font)

    # 2. Product Image Container (Clean White Card with Drop Shadow)
    draw.rounded_rectangle([(100, 240), (980, 1080)], radius=40, fill=(255, 255, 255))
    
    # Load and paste product image
    img_path = download_product_image(deal.get("image_url"), deal["asin"], deal["title"])
    try:
        p_img = Image.open(img_path).convert("RGBA")
        p_img.thumbnail((800, 760), Image.Resampling.LANCZOS)
        offset_x = 100 + (880 - p_img.width) // 2
        offset_y = 240 + (840 - p_img.height) // 2
        img.paste(p_img, (offset_x, offset_y), p_img)
    except Exception as e:
        print(f"Error drawing product image: {e}")

    # Discount / Hook Badge Overlaid on Product Card (top-right)
    draw.rounded_rectangle([(700, 260), (960, 360)], radius=20, fill=badge_color)
    if deal.get("discount", 0) > 0 and deal["price"] > 0:
        draw.text((730, 280), f"-{deal['discount']}%", fill=(255, 255, 255), font=get_font(48, bold=True))
        draw.text((750, 330), "OFF", fill=(255, 255, 255), font=get_font(24, bold=True))
    else:
        draw.text((720, 290), "FREE", fill=(255, 255, 255), font=get_font(42, bold=True))
        draw.text((730, 332), "ACCESS", fill=(255, 255, 255), font=get_font(20, bold=True))

    # 3. Product Title (Two lines max)
    title = deal["title"]
    if len(title) > 42:
        title_line1 = title[:40].rsplit(" ", 1)[0]
        title_line2 = title[len(title_line1):].strip()[:40]
    else:
        title_line1 = title
        title_line2 = ""

    t_font = get_font(42, bold=True)
    draw.text((100, 1130), title_line1, fill=(255, 255, 255), font=t_font)
    if title_line2:
        draw.text((100, 1185), title_line2, fill=(203, 213, 225), font=t_font)

    # 4. Pricing Box
    box_y = 1270
    draw.rounded_rectangle([(80, box_y), (1000, box_y + 260)], radius=30, fill=price_box_color)
    
    # Strikethrough MRP
    if deal['mrp'] > 0:
        draw.text((120, box_y + 30), f"MRP: ₹{deal['mrp']:,}", fill=(148, 163, 184), font=get_font(38))
        draw.line([(115, box_y + 55), (380, box_y + 55)], fill=(239, 68, 68), width=4)

    # Big Deal Price
    if deal['price'] > 0:
        price_text = f"Deal Price: ₹{deal['price']:,}"
    else:
        price_text = "100% Free AI Deal Radar"
    draw.text((120, box_y + 85), price_text, fill=accent_color, font=get_font(68, bold=True))

    # Savings Pill
    draw.rounded_rectangle([(120, box_y + 185), (650, box_y + 240)], radius=15, fill=(16, 185, 129))
    if deal['savings'] > 0 and deal['price'] > 0:
        savings_text = f"YOU SAVE FLAT ₹{deal['savings']:,} ({deal['discount']}% OFF)"
    else:
        savings_text = "UNLIMITED FREE DEALS 24/7"
    draw.text((140, box_y + 195), savings_text, fill=(255, 255, 255), font=get_font(26, bold=True))

    # 5. Social Proof / Ratings
    rating_y = 1570
    draw.text((100, rating_y), f"⭐ {deal['rating']} / 5.0 Rating  |  {deal['reviews']:,}+ Verified Buyers", fill=(251, 191, 36), font=get_font(34, bold=True))

    # 6. Bottom Call to Action Banner
    draw.rounded_rectangle([(80, 1660), (1000, 1840)], radius=30, fill=(37, 99, 235))
    cta_title = "👇 TAP LINK IN BIO / COMMENT 👇" if slide_idx != 2 else "🚀 JOIN WHATSAPP & TELEGRAM VIP"
    cta_sub = "Verified Amazon India Affiliate Link" if slide_idx != 2 else "Visit BharatBazaro.com for daily loot drops"
    draw.text((130, 1700), cta_title, fill=(255, 255, 255), font=get_font(38, bold=True))
    draw.text((220, 1765), cta_sub, fill=(219, 234, 254), font=get_font(28))

    slide_path = OUTPUT_DIR / f"{deal['asin']}_slide_{slide_idx}.png"
    img.save(slide_path, quality=95)
    return slide_path

async def generate_narration(script_text: str, voice: str, output_path: Path):
    """Generate audio using free Microsoft Edge TTS."""
    import edge_tts
    communicate = edge_tts.Communicate(script_text, voice)
    await communicate.save(str(output_path))

def build_deal_script(deal: dict, language: str = "en") -> str:
    """Compose punchy Hook-Story-Offer script tailored to 20-30s Short."""
    if "custom_script" in deal:
        return deal["custom_script"]

    if language == "hi":
        return (
            f"Amazon India par zabardast loot deal alert! "
            f"{deal['title']} jiska original MRP {deal['mrp']} rupaye hai, "
            f"aaj mil raha hai flat {deal['discount']} percent discount par, sirf {deal['price']} rupaye mein! "
            f"Aapki seedhi bachat hogi {deal['savings']} rupaye ki! "
            f"{deal['rating']} star rating aur {deal['reviews']:,} se zyaada customer reviews ke saath ye deal limited time ke liye hai. "
            f"Abhi buy karne ke liye bio ya comment section mein affiliate link check karein, "
            f"aur rozaana aisi price drops ke liye BharatBazaro ko follow karein!"
        )
    else:
        return (
            f"Loot Deal Alert on Amazon India! "
            f"The top-selling {deal['title']} with MRP {deal['mrp']} rupees, "
            f"is crashing today at a massive {deal['discount']} percent discount, for just {deal['price']} rupees! "
            f"You save a flat {deal['savings']} rupees instantly! "
            f"Rated {deal['rating']} stars with over {deal['reviews']:,} verified reviews. "
            f"This price drop won't last long. "
            f"Tap the affiliate link in our bio or comments to order now, and join BharatBazaro for daily loot deals!"
        )

def get_audio_duration(audio_file: Path) -> float:
    """Use FFprobe / FFmpeg to inspect audio duration."""
    cmd = [
        FFMPEG_EXE, "-i", str(audio_file)
    ]
    res = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    for line in res.stderr.splitlines():
        if "Duration:" in line:
            parts = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = parts.split(":")
            return float(h) * 3600 + float(m) * 60 + float(s)
    return 20.0

def assemble_short_video(deal: dict, slides: list[Path], audio_path: Path, output_video: Path):
    """
    Assemble high-production 9:16 vertical video using FFmpeg.
    Adds smooth Ken-Burns pan/zoom and mixes narration with unique background music.
    """
    total_duration = get_audio_duration(audio_path)
    slide_duration = total_duration / len(slides)
    
    # 1. Generate video clips from each slide with zoompan
    clip_files = []
    fps = 30
    for idx, slide in enumerate(slides):
        clip_path = OUTPUT_DIR / f"{deal['asin']}_clip_{idx}.mp4"
        frames = int(slide_duration * fps)
        
        # Alternate zoom styles for unique feel
        if idx == 0:
            zoom_filter = f"zoompan=z='min(zoom+0.0010,1.10)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps={fps}"
        elif idx == 1:
            zoom_filter = f"zoompan=z='if(lte(zoom,1.0),1.10,max(1.0,zoom-0.0010))':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps={fps}"
        else:
            zoom_filter = f"zoompan=z='min(zoom+0.0008,1.08)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)+15':s=1080x1920:fps={fps}"

        cmd = [
            FFMPEG_EXE, "-y",
            "-loop", "1",
            "-i", str(slide),
            "-vf", zoom_filter,
            "-t", f"{slide_duration:.2f}",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            str(clip_path)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        clip_files.append(clip_path)

    # 2. Concat clips into visual track
    concat_list = OUTPUT_DIR / f"{deal['asin']}_concat.txt"
    with open(concat_list, "w") as f:
        for clip in clip_files:
            f.write(f"file '{clip.as_posix()}'\n")

    video_only = OUTPUT_DIR / f"{deal['asin']}_visual.mp4"
    cmd_concat = [
        FFMPEG_EXE, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_list),
        "-c", "copy",
        str(video_only)
    ]
    subprocess.run(cmd_concat, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    # 3. Check for specific background music for this deal
    theme = deal.get("theme", {})
    bgm_filename = theme.get("bgm", "output001.mp3")
    bgm_path = BASE_DIR / "resource" / "songs" / bgm_filename
    if not bgm_path.exists():
        bgm_path = BASE_DIR / "resource" / "songs" / "output001.mp3"
    
    if bgm_path.exists():
        # Mix narration (100% volume) + BGM (12% volume ducked)
        filter_complex = (
            f"[1:a]volume=1.0[voice];"
            f"[2:a]volume=0.12,aloop=loop=-1:size=2e+09[bgm];"
            f"[voice][bgm]amix=inputs=2:duration=first[outa]"
        )
        cmd_final = [
            FFMPEG_EXE, "-y",
            "-i", str(video_only),
            "-i", str(audio_path),
            "-i", str(bgm_path),
            "-filter_complex", filter_complex,
            "-map", "0:v",
            "-map", "[outa]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            str(output_video)
        ]
    else:
        cmd_final = [
            FFMPEG_EXE, "-y",
            "-i", str(video_only),
            "-i", str(audio_path),
            "-map", "0:v",
            "-map", "1:a",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            str(output_video)
        ]
    
    subprocess.run(cmd_final, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return output_video

def generate_single_video(deal: dict, lang: str = None, voice: str = None) -> Path:
    """Generate one complete unique video for a deal."""
    lang = lang or deal.get("default_lang", "hi")
    voice = voice or deal.get("default_voice")
    if not voice:
        voice = "hi-IN-MadhurNeural" if lang == "hi" else "en-IN-PrabhatNeural"

    print(f"\n=======================================================")
    print(f"🎬 Generating UNIQUE Short: {deal['title']}")
    print(f"💰 Deal: ₹{deal['price']:,} (MRP: ₹{deal['mrp']:,} | -{deal['discount']}%)")
    print(f"🎨 Theme: {deal.get('theme', {}).get('header_text', 'Default')} | Voice: {voice}")
    print(f"=======================================================")

    # Step 1: Visual Cards
    print("[1/4] 🎨 Designing 1080x1920 (9:16) Unique Visual Cards...")
    slides = [create_slide_image(deal, i) for i in range(3)]
    for s in slides:
        print(f"  ✓ Created {s.name}")

    # Step 2: Voiceover
    print(f"[2/4] 🎙️ Synthesizing Voiceover ({voice})...")
    script_text = build_deal_script(deal, lang)
    audio_path = OUTPUT_DIR / f"{deal['asin']}_voice.mp3"
    asyncio.run(generate_narration(script_text, voice, audio_path))
    duration = get_audio_duration(audio_path)
    print(f"  ✓ Voice complete ({duration:.1f}s)")

    # Step 3: Video Assembly
    output_video = OUTPUT_DIR / f"bharatbazaro_{deal['asin']}_{lang}.mp4"
    print(f"[3/4] 🎞️ Assembling Final HD Video with Ken Burns Zoom & BGM...")
    assemble_short_video(deal, slides, audio_path, output_video)

    # Step 4: Verification
    size_mb = output_video.stat().st_size / (1024 * 1024)
    print(f"[4/4] ✅ Done: {output_video.name} ({size_mb:.2f} MB, {duration:.1f}s)")
    return output_video

def main():
    parser = argparse.ArgumentParser(description="Generate 100% Free BharatBazaro Deal Videos")
    parser.add_argument("--asin", type=str, default="", help="Amazon ASIN (default: first deal)")
    parser.add_argument("--lang", type=str, default="", choices=["", "en", "hi"], help="Voice language")
    parser.add_argument("--voice", type=str, default="", help="Edge TTS voice name")
    parser.add_argument("--all", action="store_true", help="Generate unique videos for ALL curated deals")
    args = parser.parse_args()

    if args.all:
        print(f"\n🚀 Generating Unique Videos for ALL {len(SAMPLE_DEALS)} Curated Deals...")
        generated = []
        for d in SAMPLE_DEALS:
            vid = generate_single_video(d)
            generated.append(vid)
        print(f"\n🎉 Successfully Generated {len(generated)} Unique Videos!")
        for g in generated:
            print(f"  📍 {g.resolve()}")
        return

    # Single deal mode
    asin = args.asin or "B09W2GFM7Y"
    deal = next((d for d in SAMPLE_DEALS if d["asin"] == asin), SAMPLE_DEALS[0])
    lang = args.lang or deal.get("default_lang", "hi")
    generate_single_video(deal, lang=lang, voice=args.voice)

if __name__ == "__main__":
    main()
