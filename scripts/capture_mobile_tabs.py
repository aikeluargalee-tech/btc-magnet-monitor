import subprocess
import os
import re
from PIL import Image

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
BRAIN_DIR = r"C:\Users\aikel\.gemini\antigravity\brain\96a1582a-0842-48ec-9390-68089e318fe5"
DIST_DIR = r"C:\Users\aikel\.gemini\antigravity\scratch\btc-magnet\dist"

with open(os.path.join(DIST_DIR, "mobile_preview.html"), "r", encoding="utf-8") as f:
    base_html = f.read()

tabs = ["radar", "telemetry", "verdict", "regimes"]
screenshots = []

for tab in tabs:
    # Set the target tab active in the HTML
    tab_html = base_html
    # Hide radar if not radar
    if tab != "radar":
        tab_html = tab_html.replace('id="tab-content-radar" class="tab-pane space-y-3.5 block"', 'id="tab-content-radar" class="tab-pane space-y-3.5 hidden"')
        tab_html = tab_html.replace(f'id="tab-content-{tab}" class="tab-pane space-y-3.5 hidden"', f'id="tab-content-{tab}" class="tab-pane space-y-3.5 block"')
        tab_html = tab_html.replace(f'id="tab-content-{tab}" class="tab-pane space-y-3 hidden"', f'id="tab-content-{tab}" class="tab-pane space-y-3 block"')
        # Update tab button highlight
        tab_html = tab_html.replace('id="nav-btn-radar" onclick="switchTab(\'radar\')" class="nav-tab flex flex-col items-center justify-center py-1.5 text-cyan-400"', 'id="nav-btn-radar" onclick="switchTab(\'radar\')" class="nav-tab flex flex-col items-center justify-center py-1.5 text-zinc-400"')
        tab_html = tab_html.replace(f'id="nav-btn-{tab}" onclick="switchTab(\'{tab}\')" class="nav-tab flex flex-col items-center justify-center py-1.5 text-zinc-400 hover:text-zinc-200"', f'id="nav-btn-{tab}" onclick="switchTab(\'{tab}\')" class="nav-tab flex flex-col items-center justify-center py-1.5 text-cyan-400"')

    temp_html_path = os.path.join(DIST_DIR, f"temp_{tab}.html")
    with open(temp_html_path, "w", encoding="utf-8") as f:
        f.write(tab_html)

    img_out = os.path.join(BRAIN_DIR, f"mobile_v2_{tab}.png")
    cmd = [
        EDGE_PATH,
        "--headless",
        "--disable-gpu",
        "--hide-scrollbars",
        "--window-size=390,844",
        f"--screenshot={img_out}",
        f"file:///{temp_html_path.replace(os.sep, '/')}"
    ]
    subprocess.run(cmd, check=True)
    if os.path.exists(img_out):
        screenshots.append(img_out)
        print(f"✓ Captured {tab} tab -> {img_out}")

# Now create a 4-panel side-by-side collage
if len(screenshots) == 4:
    imgs = [Image.open(p) for p in screenshots]
    # Resize to 360 x 780 for crisp side-by-side
    target_w, target_h = 360, 780
    resized = [im.resize((target_w, target_h), Image.Resampling.LANCZOS) for im in imgs]

    total_w = target_w * 4 + 30 * 5
    total_h = target_h + 100
    collage = Image.new("RGB", (total_w, total_h), (9, 9, 11))

    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(collage)

    titles = ["1. 🧲 RADAR (OVERVIEW)", "2. 📊 TELEMETRY GRID", "3. 🧠 VERDICT METHODS", "4. 📘 REGIMES GUIDE"]

    for idx, (im, title) in enumerate(zip(resized, titles)):
        x = 30 + idx * (target_w + 30)
        y = 70
        # Draw frame border
        draw.rectangle([x-2, y-2, x+target_w+2, y+target_h+2], outline=(39, 39, 42), width=2)
        collage.paste(im, (x, y))
        draw.text((x + 10, 30), title, fill=(244, 244, 245))

    collage_path = os.path.join(BRAIN_DIR, "mobile_v2_4tab_showcase.png")
    collage.save(collage_path, "PNG")
    print(f"✓ Generated full 4-tab collage -> {collage_path}")
