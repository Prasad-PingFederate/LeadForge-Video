"""
BharatBazaro Deal Short Generator (LeadForge-Video)
Generates high-converting 9:16 vertical videos (YouTube Shorts / Instagram Reels / WhatsApp Status)
for Amazon deals with ZERO external paid models and ZERO API costs.

Voice: Microsoft Edge TTS (100% Free, unlimited, natural Indian voices)
Video Engine: Local FFmpeg (Bundled via imageio-ffmpeg)
Visuals: Dynamic 1080x1920 PIL slides with Amazon deal imagery & price badges
"""

import os
import sys
import argparse
import asyncio
import subprocess
import requests
from io import BytesIO
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

# 10 Curated High-Converting Deals & Brand Promos
SAMPLE_DEALS = [
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
        "image_url": "https://m.media-amazon.com/images/I/71uQaPuz8jL._SL600_.jpg",
        "affiliate_url": "https://www.amazon.in/dp/B002MPPTB8?tag=dammaiprasad-21",
        "default_lang": "hi",
        "default_voice": "hi-IN-MadhurNeural"
    },
    {
        "asin": "BHARATBAZARO_RADAR",
        "title": "BharatBazaro 24/7 AI Deal Radar for Amazon India",
        "category": "Shopping & Deals",
        "mrp": 9999,
        "price": 0,
        "discount": 100,
        "savings": 9999,
        "rating": 4.9,
        "reviews": 15000,
        "image_url": "https://m.media-amazon.com/images/I/71VjXyGfW2L._SL600_.jpg",
        "affiliate_url": "https://bharatbazaro.com",
        "default_lang": "en",
        "default_voice": "en-IN-NeerjaNeural",
        "custom_script": (
            "Hey! Are you still searching Amazon for hours hoping to find a good deal? "
            "Meet BharatBazaro — India's 24/7 AI Deal Radar. "
            "It automatically scans thousands of Amazon India products every few minutes and finds real price drops, "
            "hidden checkbox coupons, and even rare price errors. "
            "Every deal comes with verified Keepa price history, so you know exactly how good the discount is. "
            "Whether you want earbuds under 999 rupees, smartwatches, home appliances, or big brand loot — "
            "BharatBazaro surfaces the best ones first. "
            "Just visit bharatbazaro.com or join our VIP Telegram channel. "
            "Stop overpaying. Start saving smarter. Link in bio!"
        )
    },
    {
        "asin": "B091CR2FXY",
        "title": "AGARO Regency Air Fryer 12L 1800W",
        "category": "Home & Kitchen",
        "mrp": 15999,
        "price": 7499,
        "discount": 53,
        "savings": 8500,
        "rating": 4.5,
        "reviews": 12800,
        "image_url": "https://m.media-amazon.com/images/I/71VjXyGfW2L._SL600_.jpg",
        "affiliate_url": "https://www.amazon.in/dp/B091CR2FXY?tag=dammaiprasad-21",
        "default_lang": "hi",
        "default_voice": "hi-IN-MadhurNeural"
    },
    {
        "asin": "B09W2GFM7Y",
        "title": "Pigeon 1.8 Litre Stainless Steel Electric Kettle",
        "category": "Home & Kitchen",
        "mrp": 1295,
        "price": 549,
        "discount": 58,
        "savings": 746,
        "rating": 4.1,
        "reviews": 94200,
        "image_url": "https://m.media-amazon.com/images/I/71h6PpGaz9L._SL600_.jpg",
        "affiliate_url": "https://www.amazon.in/dp/B09W2GFM7Y?tag=dammaiprasad-21",
        "default_lang": "hi",
        "default_voice": "hi-IN-SwaraNeural"
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
        "image_url": "https://m.media-amazon.com/images/I/51HBom8xz7L._SL600_.jpg",
        "affiliate_url": "https://www.amazon.in/dp/B09NVPSCQT?tag=dammaiprasad-21",
        "default_lang": "en",
        "default_voice": "en-IN-PrabhatNeural"
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
        "image_url": "https://m.media-amazon.com/images/I/61y2VVWcGBL._SL600_.jpg",
        "affiliate_url": "https://www.amazon.in/dp/B0BY2W1H1S?tag=dammaiprasad-21",
        "default_lang": "hi",
        "default_voice": "hi-IN-MadhurNeural"
    },
    {
        "asin": "B08F9G3Y8D",
        "title": "Philips All-in-One Multi Grooming Kit 9-in-1",
        "category": "Personal Care",
        "mrp": 2295,
        "price": 1449,
        "discount": 37,
        "savings": 846,
        "rating": 4.4,
        "reviews": 51200,
        "image_url": "https://m.media-amazon.com/images/I/61K8Q-M2g8L._SL600_.jpg",
        "affiliate_url": "https://www.amazon.in/dp/B08F9G3Y8D?tag=dammaiprasad-21",
        "default_lang": "en",
        "default_voice": "en-IN-NeerjaNeural"
    },
    {
        "asin": "B09VDN3T3D",
        "title": "Portronics Power Bank 10000mAh 22.5W Fast Charging",
        "category": "Mobile Accessories",
        "mrp": 1999,
        "price": 799,
        "discount": 60,
        "savings": 1200,
        "rating": 4.3,
        "reviews": 18900,
        "image_url": "https://m.media-amazon.com/images/I/61Nl5zGZ3RL._SL600_.jpg",
        "affiliate_url": "https://www.amazon.in/dp/B09VDN3T3D?tag=dammaiprasad-21",
        "default_lang": "hi",
        "default_voice": "hi-IN-SwaraNeural"
    },
    {
        "asin": "B08HV2R8C2",
        "title": "Wipro 16A Smart WiFi Plug with Energy Monitoring",
        "category": "Smart Home",
        "mrp": 1490,
        "price": 649,
        "discount": 56,
        "savings": 841,
        "rating": 4.2,
        "reviews": 23400,
        "image_url": "https://m.media-amazon.com/images/I/61m1R5p3NfL._SL600_.jpg",
        "affiliate_url": "https://www.amazon.in/dp/B08HV2R8C2?tag=dammaiprasad-21",
        "default_lang": "en",
        "default_voice": "en-IN-PrabhatNeural"
    },
    {
        "asin": "BHARATBAZARO_LOOT_ALERT",
        "title": "Stop Paying Full Price on Amazon India! Loot Deal Alert",
        "category": "Exclusive Deals",
        "mrp": 4999,
        "price": 999,
        "discount": 80,
        "savings": 4000,
        "rating": 4.9,
        "reviews": 42000,
        "image_url": "https://m.media-amazon.com/images/I/71uQaPuz8jL._SL600_.jpg",
        "affiliate_url": "https://bharatbazaro.com",
        "default_lang": "en",
        "default_voice": "en-IN-NeerjaNeural",
        "custom_script": (
            "Wait, don’t buy that on Amazon yet! "
            "Did you know 80% of massive price drops and coupon glitches on Amazon India expire in under 30 minutes? "
            "That’s why thousands of smart shoppers use BharatBazaro. "
            "It’s an AI deal radar that scans Amazon India 24/7. "
            "When branded cookware crashes, or premium electronics get a secret 60% checkbox coupon, "
            "BharatBazaro alerts you immediately. "
            "Every single deal is Keepa-verified — zero fake MRP markups, only real historic lows. "
            "Stop wasting money. Visit bharatbazaro.com or tap the link in bio to join our VIP Telegram channel right now!"
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

def download_product_image(url: str, asin: str) -> Path:
    """Download Amazon product image or return cached image."""
    local_path = CACHE_DIR / f"{asin}.jpg"
    if local_path.exists() and local_path.stat().st_size > 5000:
        return local_path
    
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            with open(local_path, "wb") as f:
                f.write(resp.content)
            return local_path
    except Exception as e:
        print(f"Warning: Failed to download image from {url}: {e}")
    
    # Generate placeholder if download fails
    placeholder = Image.new("RGB", (600, 600), color=(240, 243, 246))
    draw = ImageDraw.Draw(placeholder)
    draw.text((150, 280), "BHARATBAZARO DEALS", fill=(100, 116, 139), font=get_font(28, bold=True))
    placeholder.save(local_path)
    return local_path

def create_slide_image(deal: dict, slide_idx: int) -> Path:
    """
    Generate professional 1080x1920 (9:16 vertical) deal visual card.
    Slide 0: Hook & Massive Price Drop
    Slide 1: Social Proof & Key Features
    Slide 2: Urgent Scarcity & Call-to-Action
    """
    width, height = 1080, 1920
    # Premium gradient background (Dark Obsidian / Slate)
    img = Image.new("RGB", (width, height), color=(11, 15, 25))
    draw = ImageDraw.Draw(img)

    # 1. Top Header Pill
    draw.rounded_rectangle([(80, 80), (1000, 180)], radius=30, fill=(220, 38, 38))
    header_text = "💥 BHARATBAZARO LOOT RADAR 💥" if slide_idx == 0 else "⭐ TOP VERIFIED AMAZON DEAL ⭐" if slide_idx == 1 else "⚡ HURRY - LIMITED TIME ONLY ⚡"
    h_font = get_font(38, bold=True)
    draw.text((120, 105), header_text, fill=(255, 255, 255), font=h_font)

    # 2. Product Image Container (White Card with Drop Shadow)
    draw.rounded_rectangle([(100, 240), (980, 1080)], radius=40, fill=(255, 255, 255))
    
    # Load and paste product image
    img_path = download_product_image(deal["image_url"], deal["asin"])
    try:
        p_img = Image.open(img_path).convert("RGBA")
        p_img.thumbnail((800, 760), Image.Resampling.LANCZOS)
        offset_x = 100 + (880 - p_img.width) // 2
        offset_y = 260 + (800 - p_img.height) // 2
        img.paste(p_img, (offset_x, offset_y), p_img)
    except Exception as e:
        print(f"Error drawing product image: {e}")

    # Discount Badge Overlaid on Product Card (top-right)
    draw.rounded_rectangle([(720, 260), (960, 360)], radius=20, fill=(234, 88, 12))
    draw.text((750, 280), f"-{deal['discount']}%", fill=(255, 255, 255), font=get_font(48, bold=True))
    draw.text((770, 330), "OFF", fill=(255, 255, 255), font=get_font(24, bold=True))

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
    draw.rounded_rectangle([(80, box_y), (1000, box_y + 260)], radius=30, fill=(24, 32, 47))
    
    # Strikethrough MRP
    if deal['mrp'] > 0:
        draw.text((120, box_y + 30), f"MRP: ₹{deal['mrp']:,}", fill=(148, 163, 184), font=get_font(38))
        draw.line([(115, box_y + 55), (380, box_y + 55)], fill=(239, 68, 68), width=4)

    # Big Deal Price
    price_text = f"Deal Price: ₹{deal['price']:,}" if deal['price'] > 0 else "Free AI Radar Access"
    draw.text((120, box_y + 85), price_text, fill=(52, 211, 153), font=get_font(68, bold=True))

    # Savings Pill
    draw.rounded_rectangle([(120, box_y + 185), (650, box_y + 240)], radius=15, fill=(16, 185, 129))
    savings_text = f"YOU SAVE FLAT ₹{deal['savings']:,} ({deal['discount']}% OFF)" if deal['savings'] > 0 else "100% FREE UNLIMITED DEALS"
    draw.text((140, box_y + 195), savings_text, fill=(255, 255, 255), font=get_font(26, bold=True))

    # 5. Social Proof / Ratings
    rating_y = 1570
    draw.text((100, rating_y), f"⭐ {deal['rating']} / 5.0 Rating  |  {deal['reviews']:,}+ Happy Users", fill=(251, 191, 36), font=get_font(34, bold=True))

    # 6. Bottom Call to Action Banner
    draw.rounded_rectangle([(80, 1660), (1000, 1840)], radius=30, fill=(37, 99, 235))
    cta_title = "👇 TAP LINK IN BIO / COMMENT 👇" if slide_idx != 2 else "🚀 JOIN WHATSAPP & TELEGRAM VIP"
    cta_sub = "Verified Amazon India Affiliate Link" if slide_idx != 2 else "Visit BharatBazaro.com for daily loot deals"
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
            f"Amazon India par loot deal alert! "
            f"{deal['title']} jiska original MRP {deal['mrp']} rupaye hai, "
            f"aaj mil raha hai flat {deal['discount']} percent discount par, sirf {deal['price']} rupaye mein! "
            f"Aapki seedhi bachat hogi {deal['savings']} rupaye ki! "
            f"4.4 star rating aur hazaaron verified customer reviews ke saath ye deal limited time ke liye hai. "
            f"Abhi buy karne ke liye bio ya comment section mein link check karein, "
            f"aur rozaana aisi loot deals ke liye BharatBazaro ko follow karein!"
        )
    else:
        return (
            f"Loot Deal Alert on Amazon India! "
            f"The popular {deal['title']} with MRP {deal['mrp']} rupees, "
            f"is crashing today at a massive {deal['discount']} percent discount, for just {deal['price']} rupees! "
            f"You save a flat {deal['savings']} rupees instantly! "
            f"Rated {deal['rating']} stars with over {deal['reviews']:,} reviews. "
            f"This lightning deal won't last long. "
            f"Tap the affiliate link in our bio or comments to order now, and join BharatBazaro for daily loot alerts!"
        )

def get_audio_duration(audio_file: Path) -> float:
    """Use FFmpeg to inspect audio duration."""
    cmd = [FFMPEG_EXE, "-i", str(audio_file)]
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
    Adds smooth Ken-Burns pan/zoom and mixes narration with background music.
    """
    total_duration = get_audio_duration(audio_path)
    slide_duration = total_duration / len(slides)
    
    # 1. Generate video clips from each slide with zoompan
    clip_files = []
    fps = 30
    for idx, slide in enumerate(slides):
        clip_path = OUTPUT_DIR / f"{deal['asin']}_clip_{idx}.mp4"
        frames = int(slide_duration * fps)
        
        # Smooth zoom in/out effect
        if idx % 2 == 0:
            zoom_filter = f"zoompan=z='min(zoom+0.0010,1.10)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps={fps}"
        else:
            zoom_filter = f"zoompan=z='if(lte(zoom,1.0),1.10,max(1.0,zoom-0.0010))':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps={fps}"

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

    # 3. Check for background music
    bgm_path = BASE_DIR / "resource" / "songs" / "output001.mp3"
    
    if bgm_path.exists():
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

def generate_single_deal_video(deal: dict, lang: str = None, voice: str = None):
    """Orchestrates generation of one complete video short."""
    lang = lang or deal.get("default_lang", "hi")
    voice = voice or deal.get("default_voice", "hi-IN-MadhurNeural" if lang == "hi" else "en-IN-PrabhatNeural")
    output_video = OUTPUT_DIR / f"bharatbazaro_{deal['asin']}_{lang}.mp4"

    print(f"\n=======================================================")
    print(f"🎬 Generating: {deal['title']}")
    print(f"💰 Deal: ₹{deal['price']:,} (MRP: ₹{deal['mrp']:,} | -{deal['discount']}%)")
    print(f"🎙️ Voice: {voice} ({lang.upper()})")
    print(f"=======================================================")

    if output_video.exists() and output_video.stat().st_size > 1000000:
        print(f"  ⚡ Video already generated at: {output_video.name} (Skipping re-render)")
        return output_video

    # 1. Slides
    slides = [create_slide_image(deal, i) for i in range(3)]
    
    # 2. Voice
    script_text = build_deal_script(deal, lang)
    audio_path = OUTPUT_DIR / f"{deal['asin']}_voice.mp3"
    asyncio.run(generate_narration(script_text, voice, audio_path))
    duration = get_audio_duration(audio_path)
    print(f"  ✓ Narration ready: {duration:.1f}s")

    # 3. Assemble
    assemble_short_video(deal, slides, audio_path, output_video)
    size_mb = output_video.stat().st_size / (1024 * 1024)
    print(f"  ✅ Render complete: {output_video.name} ({size_mb:.2f} MB | {duration:.1f}s)")
    return output_video

def main():
    parser = argparse.ArgumentParser(description="Generate 100% Free BharatBazaro Deal Videos")
    parser.add_argument("--asin", type=str, default="", help="Single ASIN to generate")
    parser.add_argument("--all", action="store_true", help="Generate all 10 curated daily videos")
    parser.add_argument("--lang", type=str, default="", choices=["", "en", "hi"], help="Voice language override")
    parser.add_argument("--voice", type=str, default="", help="Edge TTS voice override")
    args = parser.parse_args()

    if args.all:
        print("\n" + "="*60)
        print("🚀 BATCH GENERATING ALL 10 DAILY BHARATBAZARO VIDEOS")
        print("="*60)
        completed = []
        for idx, deal in enumerate(SAMPLE_DEALS, 1):
            print(f"\n[{idx}/10] Processing {deal['asin']}...")
            v = generate_single_deal_video(deal, lang=args.lang or None, voice=args.voice or None)
            completed.append(v)
        print("\n" + "="*60)
        print(f"🎉 ALL 10 VIDEOS READY IN {OUTPUT_DIR.resolve()}")
        print("="*60)
        for idx, v in enumerate(completed, 1):
            print(f"  {idx}. {v.name} ({v.stat().st_size / (1024*1024):.2f} MB)")
    else:
        asin = args.asin or SAMPLE_DEALS[0]["asin"]
        deal = next((d for d in SAMPLE_DEALS if d["asin"] == asin), SAMPLE_DEALS[0])
        generate_single_deal_video(deal, lang=args.lang or None, voice=args.voice or None)

if __name__ == "__main__":
    main()
