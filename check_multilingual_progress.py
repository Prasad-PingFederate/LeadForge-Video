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

out = Path('C:/B4igoAnti/LeadForge-Video/output')

print(f"{'#':2} | {'Product Name':30} | {'Telugu (TE)':14} | {'English (EN)':14} | {'Hindi (HI)':14}")
print("-" * 80)
total_completed = 0
for idx, (asin, name) in enumerate(asins, 1):
    te = out / f"bharatbazaro_{asin}_te.mp4"
    en = out / f"bharatbazaro_{asin}_en.mp4"
    hi = out / f"bharatbazaro_{asin}_hi.mp4"
    
    te_str = f"{te.stat().st_size / (1024*1024):.1f} MB" if te.exists() else "..."
    en_str = f"{en.stat().st_size / (1024*1024):.1f} MB" if en.exists() else "..."
    hi_str = f"{hi.stat().st_size / (1024*1024):.1f} MB" if hi.exists() else "..."
    
    if te.exists(): total_completed += 1
    if en.exists(): total_completed += 1
    if hi.exists(): total_completed += 1
    
    print(f"{idx:2} | {name:30} | {te_str:14} | {en_str:14} | {hi_str:14}")

print(f"\nCompleted: {total_completed} / 30 videos")
