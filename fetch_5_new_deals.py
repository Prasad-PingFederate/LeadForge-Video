import asyncio
import json
import re
import requests
from pathlib import Path
from PIL import Image
from playwright.async_api import async_playwright

CACHE_DIR = Path(r"C:\B4igoAnti\LeadForge-Video\storage\deal_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

CANDIDATES = [
    {
        "asin": "B0863TXGM4",
        "search_query": "L'Oreal Paris Extraordinary Clay Shampoo 650ml B0863TXGM4",
        "title": "L'Oreal Paris Extraordinary Clay Purifying Shampoo (650ml)",
        "category": "Beauty & Personal Care",
        "mrp": 899,
        "price": 499,
        "discount": 45,
        "savings": 400,
        "rating": 4.4,
        "reviews": 19500,
        "lang": "en",
        "voice": "en-IN-NeerjaNeural",
        "theme": {
            "bg_color": (19, 78, 74),           # Deep Cyan / Teal
            "header_color": (13, 148, 136),     # Teal
            "header_text": "✨ HAIRCARE MEGA SAVINGS ✨",
            "price_box_color": (17, 94, 89),
            "accent_color": (45, 212, 191),
            "badge_color": (219, 39, 119),      # Pink
            "bgm": "output008.mp3",
            "hook_badge": "🔥 45% OFF BEAUTY LOOT"
        }
    },
    {
        "asin": "B07RJWB549",
        "search_query": "Lakme Eyeconic Kajal Twin Pack Deep Black B07RJWB549",
        "title": "Lakme Eyeconic Kajal Twin Pack Deep Black 2x0.35g",
        "category": "Beauty & Cosmetics",
        "mrp": 450,
        "price": 260,
        "discount": 42,
        "savings": 190,
        "rating": 4.3,
        "reviews": 31000,
        "lang": "hi",
        "voice": "hi-IN-SwaraNeural",
        "theme": {
            "bg_color": (24, 24, 27),           # Obsidian Black
            "header_color": (219, 39, 119),     # Magenta / Pink
            "header_text": "💄 LAKME TWIN PACK DEAL 💄",
            "price_box_color": (39, 39, 42),
            "accent_color": (244, 114, 182),
            "badge_color": (220, 38, 38),
            "bgm": "output009.mp3",
            "hook_badge": "⭐ 31,000+ REVIEWS"
        }
    },
    {
        "asin": "B08TV2P1N8",
        "search_query": "boAt Rockerz 255 Pro+ Bluetooth Neckband B08TV2P1N8",
        "title": "boAt Rockerz 255 Pro+ Wireless Neckband 40H Playtime",
        "category": "Electronics & Audio",
        "mrp": 3990,
        "price": 899,
        "discount": 77,
        "savings": 3091,
        "rating": 4.1,
        "reviews": 162000,
        "lang": "hi",
        "voice": "hi-IN-MadhurNeural",
        "theme": {
            "bg_color": (15, 23, 42),           # Cyber Slate
            "header_color": (234, 88, 12),      # Flame Orange
            "header_text": "🎧 77% OFF BOAT LOOT DEAL 🎧",
            "price_box_color": (30, 41, 59),
            "accent_color": (251, 191, 36),
            "badge_color": (220, 38, 38),
            "bgm": "output011.mp3",
            "hook_badge": "🔥 FLAT ₹3,091 SAVINGS"
        }
    },
    {
        "asin": "B0073QO2G8",
        "search_query": "Milton Thermosteel Flip Lid Flask 1000ml B0073QO2G8",
        "title": "Milton Thermosteel Flip Lid Stainless Steel Flask 1000ml",
        "category": "Home & Kitchen",
        "mrp": 1285,
        "price": 899,
        "discount": 30,
        "savings": 386,
        "rating": 4.3,
        "reviews": 42000,
        "lang": "en",
        "voice": "en-IN-PrabhatNeural",
        "theme": {
            "bg_color": (30, 27, 75),           # Deep Indigo
            "header_color": (37, 99, 235),      # Royal Blue
            "header_text": "❄️ 24HR HOT & COLD FLASK ❄️",
            "price_box_color": (49, 46, 129),
            "accent_color": (96, 165, 250),
            "badge_color": (16, 185, 129),
            "bgm": "output012.mp3",
            "hook_badge": "⭐ 24H TEMPERATURE LOCK"
        }
    },
    {
        "asin": "B07NSS9L3G",
        "search_query": "Wipro 9W Smart LED Bulb B07NSS9L3G",
        "title": "Wipro 9W Wi-Fi Smart LED Bulb 16 Million Colors",
        "category": "Smart Home & Lighting",
        "mrp": 1090,
        "price": 499,
        "discount": 54,
        "savings": 591,
        "rating": 4.2,
        "reviews": 56000,
        "lang": "hi",
        "voice": "hi-IN-SwaraNeural",
        "theme": {
            "bg_color": (88, 28, 135),          # Royal Violet
            "header_color": (124, 58, 237),     # Electric Violet
            "header_text": "💡 16M COLOR SMART BULB 💡",
            "price_box_color": (107, 33, 168),
            "accent_color": (244, 114, 182),
            "badge_color": (245, 158, 11),
            "bgm": "output013.mp3",
            "hook_badge": "🚀 54% OFF TECH DROP"
        }
    }
]

async def resolve_images():
    print("Launching Playwright to inspect exact Amazon India product images...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = await context.new_page()

        results = []
        for item in CANDIDATES:
            asin = item["asin"]
            local_path = CACHE_DIR / f"{asin}.jpg"
            
            # Search Amazon India
            url = f"https://www.amazon.in/s?k={item['asin']}"
            print(f"\nScanning: {item['title']} ({asin})...")
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=25000)
                await page.wait_for_timeout(1500)
                
                # Extract image src from search results
                img_srcs = await page.evaluate('''() => {
                    const imgs = Array.from(document.querySelectorAll('img.s-image'));
                    return imgs.map(i => i.src);
                }''')

                clean_url = None
                for src in img_srcs:
                    if "images/I/" in src:
                        # Strip sizing modifiers to get high-res original
                        clean_url = re.sub(r'\._[A-Z0-9_,]+_\.', '.', src)
                        break

                if clean_url:
                    print(f"  Found Amazon Image: {clean_url}")
                    # Download original image
                    resp = requests.get(clean_url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
                    if resp.status_code == 200 and len(resp.content) > 15000:
                        with open(local_path, "wb") as f:
                            f.write(resp.content)
                        im = Image.open(local_path)
                        item["image_url"] = clean_url
                        item["image_size"] = f"{im.width}x{im.height} ({len(resp.content)} bytes)"
                        print(f"  ✓ Verified and cached: {item['image_size']}")
                    else:
                        print(f"  ⚠️ Bad response or file too small: {resp.status_code}")
                else:
                    print("  ⚠️ No image src found on search page")
            except Exception as e:
                print(f"  ⚠️ Error scanning {asin}: {e}")

        await browser.close()
    
    with open(CACHE_DIR / "new_5_deals.json", "w") as f:
        json.dump(CANDIDATES, f, indent=2)
    print("\nSaved new_5_deals.json!")

if __name__ == "__main__":
    asyncio.run(resolve_images())
