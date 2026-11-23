import os
from pathlib import Path

base_dir = Path(r"C:\B4igoAnti\LeadForge-Video")
en_path = base_dir / "README-en.md"
out_path = base_dir / "README.md"

with open(en_path, "r", encoding="utf-8") as f:
    en_content = f.read()

header = """<div align="center">

# LeadForge-Video 🎬💸

### Automated Short Video Engine for BharatBazaro & Deal Conversions
*Generate high-converting 9:16 vertical shorts for YouTube Shorts, Instagram Reels, and WhatsApp Status with ZERO paid AI models and ZERO API costs.*

[![Version](https://img.shields.io/badge/version-v1.3.10-blue)](https://github.com/Prasad-PingFederate/LeadForge-Video)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](https://github.com/Prasad-PingFederate/LeadForge-Video)
[![Python](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

English | [简体中文](README-zh.md) | [日本語](README-ja.md)

</div>

---

## ⚡ Featured: BharatBazaro Deal Short Generator (`generate_deal_short.py`)

LeadForge-Video includes a dedicated generator tailored for e-commerce and affiliate marketing (Amazon India / BharatBazaro):

```bash
# Generate a vertical deal short in Hindi (Microsoft Edge TTS)
python generate_deal_short.py --asin B002MPPTB8 --lang hi

# Generate in Indian English
python generate_deal_short.py --asin B002MPPTB8 --lang en
```

### Key Highlights:
* **₹0.00 Running Cost**: Powered by Microsoft Edge TTS (`hi-IN-MadhurNeural`, `en-IN-PrabhatNeural`) — 100% free, natural-sounding, no API keys needed.
* **Local Offline Rendering**: Local FFmpeg applies smooth Ken Burns zoom animations, text banners, and discount math.
* **Dynamic Deal Cards**: Automatically builds 1080x1920 vertical slides showing product images, MRP strikethrough, discount badge (-53%), and rupees saved.
* **Direct Affiliate Attribution**: Automatically embeds your Amazon Affiliate Tag (`tag=dammaiprasad-21`) and call-to-actions.

---

"""

idx = en_content.find("## Screenshots")
if idx != -1:
    body = en_content[idx:]
else:
    body = en_content

full_readme = header + body

with open(out_path, "w", encoding="utf-8") as f:
    f.write(full_readme)

print(f"Successfully generated 100% English README.md! Total characters: {len(full_readme)}")
