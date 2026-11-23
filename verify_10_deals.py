from PIL import Image
from pathlib import Path

asins = [
    ('B09W2GFM7Y', 'Pigeon 1.8L Kettle'),
    ('B08F9G3Y8D', 'Philips Multi Grooming Kit'),
    ('B09VDN3T3D', 'Portronics 22.5W Power Bank'),
    ('B091CR2FXY', 'AGARO 12L Air Fryer'),
    ('B002MPPTB8', 'Hawkins Pressure Cooker'),
    ('B09NVPSCQT', 'Noise Buds VS102 Earbuds'),
    ('B0BY2W1H1S', 'Fastrack Limitless Smartwatch'),
    ('B07RJWB549', 'Lakme Eyeconic Kajal Twin Pack'),
    ('B08TV2P1N8', 'boAt Rockerz 255 Pro+ Neckband'),
    ('B07NSS9L3G', 'Wipro 9W Smart LED Bulb')
]

for idx, (asin, name) in enumerate(asins, 1):
    p = Path(f'storage/deal_cache/{asin}.jpg')
    if p.exists():
        im = Image.open(p)
        print(f"{idx:2}. {name:32} | ASIN: {asin} | Res: {im.width}x{im.height} | FileSize: {p.stat().st_size:,} bytes | STATUS: OK")
    else:
        print(f"{idx:2}. {name:32} | ASIN: {asin} | STATUS: MISSING")
