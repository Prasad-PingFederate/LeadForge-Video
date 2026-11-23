"""
BharatBazaro Multilingual 30-Video Generator (10 Products x 3 Languages)
Generates:
- 10 Telugu Deals (te-IN-MohanNeural / te-IN-ShrutiNeural)
- 10 English Deals (en-IN-PrabhatNeural / en-IN-NeerjaNeural)
- 10 Hindi Deals (hi-IN-MadhurNeural / hi-IN-SwaraNeural)

Video visuals are rendered ONCE per deal with verified 2000px+ Amazon assets,
and language audios are synthesized and muxed cleanly via stream loop.
"""

import os
import sys
import asyncio
import subprocess
import requests
import json
import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
CACHE_DIR = BASE_DIR / "storage" / "deal_cache"
CACHE_DIR.mkdir(exist_ok=True, parents=True)

FFMPEG_EXE = r"C:\Users\prasad.dammai\AppData\Roaming\Python\Python315\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
if not Path(FFMPEG_EXE).exists():
    import imageio_ffmpeg
    FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

DEALS = [
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
        "affiliate_url": "https://www.amazon.in/dp/B09W2GFM7Y?tag=dammaiprasad-21",
        "theme": {
            "bg_color": (30, 27, 75),           # Deep Indigo
            "header_color": (234, 88, 12),      # Flame Orange
            "header_text": "🔥 HOSTEL & HOME MUST-HAVE 🔥",
            "price_box_color": (49, 46, 129),
            "accent_color": (251, 191, 36),
            "badge_color": (220, 38, 38),
            "bgm": "output003.mp3",
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
        "affiliate_url": "https://www.amazon.in/dp/B08F9G3Y8D?tag=dammaiprasad-21",
        "theme": {
            "bg_color": (24, 24, 27),           # Obsidian Black
            "header_color": (37, 99, 235),      # Philips Royal Blue
            "header_text": "✨ PHILIPS SALON PRECISION ✨",
            "price_box_color": (39, 39, 42),
            "accent_color": (96, 165, 250),
            "badge_color": (217, 119, 6),
            "bgm": "output006.mp3",
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
        "affiliate_url": "https://www.amazon.in/dp/B09VDN3T3D?tag=dammaiprasad-21",
        "theme": {
            "bg_color": (88, 28, 135),          # Royal Violet
            "header_color": (219, 39, 119),     # Pink / Magenta
            "header_text": "🔋 POCKET POWER BANK LOOT 🔋",
            "price_box_color": (107, 33, 168),
            "accent_color": (244, 114, 182),
            "badge_color": (245, 158, 11),
            "bgm": "output007.mp3",
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
        "affiliate_url": "https://www.amazon.in/dp/B091CR2FXY?tag=dammaiprasad-21",
        "theme": {
            "bg_color": (6, 78, 59),            # Emerald Forest
            "header_color": (16, 185, 129),     # Emerald Green
            "header_text": "⚡ 53% OFF MASSIVE PRICE DROP ⚡",
            "price_box_color": (4, 47, 46),
            "accent_color": (52, 211, 153),
            "badge_color": (217, 119, 6),
            "bgm": "output002.mp3",
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
        "affiliate_url": "https://www.amazon.in/dp/B002MPPTB8?tag=dammaiprasad-21",
        "theme": {
            "bg_color": (15, 23, 42),           # Slate Navy
            "header_color": (220, 38, 38),       # Kitchen Crimson
            "header_text": "💥 BHARATBAZARO KITCHEN LOOT 💥",
            "price_box_color": (30, 41, 59),
            "accent_color": (245, 158, 11),
            "badge_color": (234, 88, 12),
            "bgm": "output001.mp3",
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
        "affiliate_url": "https://www.amazon.in/dp/B09NVPSCQT?tag=dammaiprasad-21",
        "theme": {
            "bg_color": (15, 23, 42),           # Cyber Slate
            "header_color": (124, 58, 237),     # Electric Purple
            "header_text": "🎧 UNDER ₹999 TECH LOOT 🎧",
            "price_box_color": (24, 24, 27),
            "accent_color": (6, 182, 212),
            "badge_color": (147, 51, 234),
            "bgm": "output004.mp3",
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
        "affiliate_url": "https://www.amazon.in/dp/B0BY2W1H1S?tag=dammaiprasad-21",
        "theme": {
            "bg_color": (19, 78, 74),           # Deep Teal
            "header_color": (13, 148, 136),     # Teal
            "header_text": "⌚ SMARTWATCH CRASH DEAL ⌚",
            "price_box_color": (17, 94, 89),
            "accent_color": (45, 212, 191),
            "badge_color": (225, 29, 72),
            "bgm": "output005.mp3",
        }
    },
    {
        "asin": "B07RJWB549",
        "title": "Lakme Eyeconic Kajal Twin Pack Deep Black 2x0.35g",
        "category": "Beauty & Cosmetics",
        "mrp": 450,
        "price": 260,
        "discount": 42,
        "savings": 190,
        "rating": 4.3,
        "reviews": 31000,
        "affiliate_url": "https://www.amazon.in/dp/B07RJWB549?tag=dammaiprasad-21",
        "theme": {
            "bg_color": (24, 24, 27),           # Obsidian Black
            "header_color": (219, 39, 119),     # Magenta / Pink
            "header_text": "💄 LAKME TWIN PACK DEAL 💄",
            "price_box_color": (39, 39, 42),
            "accent_color": (244, 114, 182),
            "badge_color": (220, 38, 38),
            "bgm": "output009.mp3",
        }
    },
    {
        "asin": "B08TV2P1N8",
        "title": "boAt Rockerz 255 Pro+ Wireless Neckband 40H Playtime",
        "category": "Electronics & Audio",
        "mrp": 3990,
        "price": 899,
        "discount": 77,
        "savings": 3091,
        "rating": 4.1,
        "reviews": 162000,
        "affiliate_url": "https://www.amazon.in/dp/B08TV2P1N8?tag=dammaiprasad-21",
        "theme": {
            "bg_color": (15, 23, 42),           # Cyber Slate
            "header_color": (234, 88, 12),      # Flame Orange
            "header_text": "🎧 77% OFF BOAT LOOT DEAL 🎧",
            "price_box_color": (30, 41, 59),
            "accent_color": (251, 191, 36),
            "badge_color": (220, 38, 38),
            "bgm": "output011.mp3",
        }
    },
    {
        "asin": "B07NSS9L3G",
        "title": "Wipro 9W Wi-Fi Smart LED Bulb 16 Million Colors",
        "category": "Smart Home & Lighting",
        "mrp": 1090,
        "price": 499,
        "discount": 54,
        "savings": 591,
        "rating": 4.2,
        "reviews": 56000,
        "affiliate_url": "https://www.amazon.in/dp/B07NSS9L3G?tag=dammaiprasad-21",
        "theme": {
            "bg_color": (88, 28, 135),          # Royal Violet
            "header_color": (124, 58, 237),     # Electric Violet
            "header_text": "💡 16M COLOR SMART BULB 💡",
            "price_box_color": (107, 33, 168),
            "accent_color": (244, 114, 182),
            "badge_color": (245, 158, 11),
            "bgm": "output013.mp3",
        }
    }
]

def get_font(size: int, bold: bool = False):
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

def create_slide_image(deal: dict, slide_idx: int) -> Path:
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
    
    draw.text((110, 108), header_text, fill=(255, 255, 255), font=get_font(36, bold=True))

    # 2. Product Image Container (White Card)
    draw.rounded_rectangle([(100, 240), (980, 1080)], radius=40, fill=(255, 255, 255))
    img_path = CACHE_DIR / f"{deal['asin']}.jpg"
    try:
        p_img = Image.open(img_path).convert("RGBA")
        p_img.thumbnail((800, 760), Image.Resampling.LANCZOS)
        offset_x = 100 + (880 - p_img.width) // 2
        offset_y = 240 + (840 - p_img.height) // 2
        img.paste(p_img, (offset_x, offset_y), p_img)
    except Exception as e:
        print(f"Error drawing product image: {e}")

    # Discount Badge Overlaid on Product Card (top-right)
    draw.rounded_rectangle([(700, 260), (960, 360)], radius=20, fill=badge_color)
    draw.text((730, 280), f"-{deal['discount']}%", fill=(255, 255, 255), font=get_font(48, bold=True))
    draw.text((750, 330), "OFF", fill=(255, 255, 255), font=get_font(24, bold=True))

    # 3. Product Title
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
    draw.text((120, box_y + 30), f"MRP: ₹{deal['mrp']:,}", fill=(148, 163, 184), font=get_font(38))
    draw.line([(115, box_y + 55), (380, box_y + 55)], fill=(239, 68, 68), width=4)

    price_text = f"Deal Price: ₹{deal['price']:,}"
    draw.text((120, box_y + 85), price_text, fill=accent_color, font=get_font(68, bold=True))

    # Savings Pill
    draw.rounded_rectangle([(120, box_y + 185), (650, box_y + 240)], radius=15, fill=(16, 185, 129))
    savings_text = f"YOU SAVE FLAT ₹{deal['savings']:,} ({deal['discount']}% OFF)"
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

def build_deal_script(deal: dict, language: str) -> str:
    """Build natural Hook-Story-Offer scripts with telugutts punctuation spacing."""
    if language == "te":
        # Telugu (Mohan / Shruti)
        return (
            f"అమెజాన్ ఇండియాలో బిగ్గెస్ట్ లూట్ డీల్ అలర్ట్! "
            f"{deal['title']}, దీని అసలు MRP {deal['mrp']} రూపాయలు, "
            f"కానీ ఈరోజు లభిస్తుంది ఫ్లాట్ {deal['discount']} శాతం డిస్కౌంట్ తో, కేవలం {deal['price']} రూపాయలకే! "
            f"మీకు నేరుగా {deal['savings']} రూపాయల భారీ బచత్ లభిస్తుంది! "
            f"{deal['rating']} స్టార్ రేటింగ్ మరియు {deal['reviews']:,} కి పైగా కస్టమర్ రివ్యూస్ ఉన్న ఈ లూట్ డీల్ పరిమిత సమయం మాత్రమే ఉంటుంది! "
            f"వెంటనే ఆర్డర్ చేయడానికి బయో లేదా కామెంట్ బాక్స్ లో ఇచ్చిన అఫీషియల్ లింక్ ని క్లిక్ చేయండి, "
            f"మరిన్ని డైలీ ఆఫర్స్ కోసం భారత్ బజారో ని ఫాలో అవ్వండి!"
        )
    elif language == "hi":
        # Hindi (Madhur / Swara)
        return (
            f"अमेज़न इंडिया पर ज़बरदस्त लूट डील अलर्ट! "
            f"{deal['title']}, जिसका ओरिजिनल एमआरपी {deal['mrp']} रुपये है, "
            f"आज मिल रहा है पूरे {deal['discount']} परसेंट डिस्काउंट पर, सिर्फ {deal['price']} रुपये में! "
            f"आपकी सीधी बचत होगी {deal['savings']} रुपये की! "
            f"{deal['rating']} स्टार रेटिंग और {deal['reviews']:,} से ज़्यादा वेरिफाइड कस्टमर रिव्यूज के साथ ये डील सीमित समय के लिए है! "
            f"अभी खरीदने के लिए बायो या कमेंट सेक्शन में दिए गए लिंक पर क्लिक करें, "
            f"और हर दिन ऐसी धांसू डील्स के लिए भारत बज़ारों को फॉलो करें!"
        )
    else:
        # English (Prabhat / Neerja)
        return (
            f"Massive Loot Deal Alert on Amazon India! "
            f"The top-rated {deal['title']} with original MRP {deal['mrp']} rupees, "
            f"is crashing today at a huge {deal['discount']} percent discount, for just {deal['price']} rupees! "
            f"You save a flat {deal['savings']} rupees instantly! "
            f"Rated {deal['rating']} stars with over {deal['reviews']:,} verified buyer reviews. "
            f"This price drop won't last long! "
            f"Tap the affiliate link in our bio or comments to order right now, and follow BharatBazaro for daily deals!"
        )

def clean_text_for_speech(text: str) -> str:
    """Normalize punctuation spacing as discovered in telugutts-frontend."""
    text = re.sub(r'([.!?।])([^\s])', r'\1 \2', text)
    text = re.sub(r',([^\s])', r', \1', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

async def generate_voice_file(text: str, voice: str, output_path: Path):
    import edge_tts
    cleaned = clean_text_for_speech(text)
    communicate = edge_tts.Communicate(cleaned, voice, rate='-5%')
    await communicate.save(str(output_path))

def get_audio_duration(audio_file: Path) -> float:
    cmd = [FFMPEG_EXE, "-i", str(audio_file)]
    res = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    for line in res.stderr.splitlines():
        if "Duration:" in line:
            parts = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = parts.split(":")
            return float(h) * 3600 + float(m) * 60 + float(s)
    return 30.0

def render_visual_track(deal: dict, slides: list[Path], target_duration: float, visual_video: Path):
    """Render 1080x1920 video with smooth Ken Burns zoom."""
    slide_dur = target_duration / len(slides)
    clip_files = []
    fps = 30
    for idx, slide in enumerate(slides):
        clip_path = OUTPUT_DIR / f"{deal['asin']}_clip_{idx}.mp4"
        frames = int(slide_dur * fps)
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
            "-t", f"{slide_dur:.2f}",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            str(clip_path)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        clip_files.append(clip_path)

    concat_list = OUTPUT_DIR / f"{deal['asin']}_concat.txt"
    with open(concat_list, "w") as f:
        for clip in clip_files:
            f.write(f"file '{clip.as_posix()}'\n")

    cmd_concat = [
        FFMPEG_EXE, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_list),
        "-c", "copy",
        str(visual_video)
    ]
    subprocess.run(cmd_concat, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

def mux_final_video(visual_video: Path, voice_path: Path, bgm_path: Path, output_file: Path):
    """Mux visual video with mixed audio track (Voice + Ducked BGM)."""
    if bgm_path.exists():
        filter_complex = (
            f"[1:a]volume=1.0[voice];"
            f"[2:a]volume=0.12,aloop=loop=-1:size=2e+09[bgm];"
            f"[voice][bgm]amix=inputs=2:duration=first[outa]"
        )
        cmd = [
            FFMPEG_EXE, "-y",
            "-stream_loop", "-1",
            "-i", str(visual_video),
            "-i", str(voice_path),
            "-i", str(bgm_path),
            "-filter_complex", filter_complex,
            "-map", "0:v",
            "-map", "[outa]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            str(output_file)
        ]
    else:
        cmd = [
            FFMPEG_EXE, "-y",
            "-stream_loop", "-1",
            "-i", str(visual_video),
            "-i", str(voice_path),
            "-map", "0:v",
            "-map", "1:a",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            str(output_file)
        ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

def process_deal_multilingual(deal: dict):
    asin = deal["asin"]
    print(f"\n=======================================================")
    print(f"🎬 Processing 3-Language Video Pack for: {deal['title']}")
    print(f"💰 ₹{deal['price']} (-{deal['discount']}%) | ASIN: {asin}")
    print(f"=======================================================")

    # Step 1: Design Slides (1080x1920)
    slides = [create_slide_image(deal, i) for i in range(3)]
    print(f"  ✓ 3 Visual Cards Ready")

    # Step 2: Render base visual video (default ~36s)
    visual_video = OUTPUT_DIR / f"{asin}_visual.mp4"
    print(f"  🎞️ Rendering Visual Motion Track once...")
    render_visual_track(deal, slides, 36.0, visual_video)
    print(f"  ✓ Visual track rendered: {visual_video.name}")

    # Step 3: Generate Audio & Mux 3 Languages
    bgm_filename = deal.get("theme", {}).get("bgm", "output001.mp3")
    bgm_path = BASE_DIR / "resource" / "songs" / bgm_filename
    if not bgm_path.exists():
        bgm_path = BASE_DIR / "resource" / "songs" / "output001.mp3"

    languages = [
        ("te", "te-IN-MohanNeural", "Telugu"),
        ("en", "en-IN-PrabhatNeural", "English"),
        ("hi", "hi-IN-MadhurNeural", "Hindi"),
    ]

    outputs = []
    for lang, voice, lang_name in languages:
        print(f"  🎙️ Synthesizing {lang_name} Audio ({voice})...")
        script = build_deal_script(deal, lang)
        voice_path = OUTPUT_DIR / f"{asin}_{lang}_voice.mp3"
        asyncio.run(generate_voice_file(script, voice, voice_path))
        dur = get_audio_duration(voice_path)

        out_video = OUTPUT_DIR / f"bharatbazaro_{asin}_{lang}.mp4"
        print(f"  ⚡ Muxing {lang_name} Video ({dur:.1f}s)...")
        mux_final_video(visual_video, voice_path, bgm_path, out_video)
        size_mb = out_video.stat().st_size / (1024 * 1024)
        print(f"  ✅ Complete: {out_video.name} ({size_mb:.2f} MB)")
        outputs.append(out_video)

    return outputs

def main():
    print(f"\n🚀 Starting BharatBazaro 30-Video Multilingual Generation...")
    print(f"📦 Total Deals: {len(DEALS)} | Languages: Telugu, English, Hindi")
    all_videos = []
    for idx, deal in enumerate(DEALS, 1):
        print(f"\n--- Deal [{idx}/{len(DEALS)}] ---")
        vids = process_deal_multilingual(deal)
        all_videos.extend(vids)

    print(f"\n🎉 ALL {len(all_videos)} MULTILINGUAL VIDEOS GENERATED SUCCESSFULLY!")
    print(f"📁 Output Directory: {OUTPUT_DIR.resolve()}")

if __name__ == "__main__":
    main()
