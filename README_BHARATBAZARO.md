# BharatBazaro Video Generation Engine (`LeadForge-Video`)

High-converting vertical deal short videos for **YouTube Shorts**, **Instagram Reels**, and **WhatsApp Status** to drive Amazon affiliate commissions (`tag=dammaiprasad-21`).

---

## ⚡ Zero-Cost Architecture (No Antigravity / No Paid Models Needed)

| Component | Provider | Cost | Why it works for BharatBazaro |
| :--- | :--- | :--- | :--- |
| **Voiceover / Narration** | **Microsoft Edge TTS** (`edge-tts`) | **₹0 (Free / Unlimited)** | Ultra-natural Indian voices (`hi-IN-MadhurNeural`, `en-IN-PrabhatNeural`) with zero API keys. |
| **Video Engine** | **FFmpeg** (Bundled via `imageio-ffmpeg`) | **₹0 (Local CPU)** | Applies Ken-Burns pan/zoom motion to product imagery, composites 1080x1920 frames, and renders MP4s. |
| **Visual Design** | **Pillow (PIL)** | **₹0 (Local)** | Generates high-contrast vertical cards with MRP slash, Deal Price, % savings pill, star rating, and CTA. |
| **Background Music** | **Bundled Royalty-Free Tracks** | **₹0 (Local)** | Built-in ambient tracks (`resource/songs/`) ducked cleanly beneath narration. |
| **Affiliate Tracking** | **Amazon Associates** | **₹0** | Automatically maps `tag=dammaiprasad-21` and BharatBazaro VIP links into video CTAs and descriptions. |

---

## 🚀 How to Generate Videos

### 1. Generate Video in Hindi (Male Voice - Madhur)
```bash
python generate_deal_short.py --asin B002MPPTB8 --lang hi
```
*Outputs:* `output/bharatbazaro_B002MPPTB8_hi.mp4` (~42 seconds, 1080x1920)

### 2. Generate Video in Indian English (Male Voice - Prabhat)
```bash
python generate_deal_short.py --asin B091CR2FXY --lang en
```
*Outputs:* `output/bharatbazaro_B091CR2FXY_en.mp4` (~43 seconds, 1080x1920)

### 3. Generate Video for Any Curated Deal
Select any ASIN from the curated deals catalog:
- `B002MPPTB8`: Hawkins Futura Pressure Cooker 3L (25% off)
- `B091CR2FXY`: AGARO Regency Air Fryer 12L (53% off - Flat ₹8,500 saving)
- `B09W2GFM7Y`: Pigeon Electric Kettle 1.8L (58% off)

---

## 📱 Supported Output Formats
- **Format**: MP4 (H.264 / AAC)
- **Aspect Ratio**: 9:16 Vertical (1080 x 1920)
- **Platforms**:
  - YouTube Shorts
  - Instagram Reels
  - WhatsApp Status / VIP Channel
  - Telegram Video Feed
