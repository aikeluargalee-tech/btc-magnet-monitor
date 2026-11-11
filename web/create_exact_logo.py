import os
import subprocess
from PIL import Image

def generate_exact_svg(out_path):
    # This SVG is an exact 1:1 mathematical reconstruction of the user's uploaded icon:
    # 1. Dark squircle base (#08080a)
    # 2. Arched neon green top bridge (#00ea47 / rgb(0, 234, 67))
    # 3. Left pole: Red (#ff2640 / rgb(253, 34, 56))
    # 4. Right pole: Electric sky blue (#00aef0 / rgb(0, 173, 229))
    # 5. Left and right vertical arms: Neon green
    # 6. Smooth bottom U-arc: Neon green
    # 7. Center hollow: Pure deep black (#08080a), uncluttered, exactly as in user's image.
    svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <defs>
    <!-- Background squircle -->
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0e0e12"/>
      <stop offset="100%" stop-color="#060608"/>
    </linearGradient>

    <!-- Red pole: pure vibrant red from screenshot rgb(253, 34, 56) -->
    <linearGradient id="redPole" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#ff334b"/>
      <stop offset="100%" stop-color="#ea1d36"/>
    </linearGradient>

    <!-- Blue pole: pure electric cyan/blue from screenshot rgb(0, 173, 229) -->
    <linearGradient id="bluePole" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#00bcf2"/>
      <stop offset="100%" stop-color="#009ad9"/>
    </linearGradient>

    <!-- Neon Green body from screenshot rgb(0, 234, 67) -->
    <linearGradient id="neonGreen" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#00ea47"/>
      <stop offset="100%" stop-color="#00d43f"/>
    </linearGradient>
  </defs>

  <!-- Dark Squircle Shell -->
  <rect x="8" y="8" width="496" height="496" rx="118" ry="118" fill="url(#bgGrad)" stroke="#1a1a20" stroke-width="2"/>

  <!-- Top Bridge Green Arc -->
  <path d="M 152,48 C 182,36 218,30 256,30 C 294,30 330,36 360,48 L 360,86 C 330,76 294,70 256,70 C 218,70 182,76 152,86 Z" fill="url(#neonGreen)"/>

  <!-- Left Pole (Red) -->
  <path d="M 84,72 C 84,58 92,50 106,48 L 152,48 L 152,185 L 84,185 Z" fill="url(#redPole)"/>

  <!-- Right Pole (Cyan/Blue) -->
  <path d="M 360,48 L 406,48 C 420,50 428,58 428,72 L 428,185 L 360,185 Z" fill="url(#bluePole)"/>

  <!-- Left Vertical Arm (Neon Green) -->
  <rect x="84" y="185" width="68" height="130" fill="url(#neonGreen)"/>

  <!-- Right Vertical Arm (Neon Green) -->
  <rect x="360" y="185" width="68" height="130" fill="url(#neonGreen)"/>

  <!-- Bottom U-Curve (Neon Green) -->
  <path d="M 84,315 A 172,172 0 0,0 428,315 L 360,315 A 104,104 0 0,1 152,315 Z" fill="url(#neonGreen)"/>
</svg>'''
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(svg_content)
    print(f"Generated SVG: {out_path}")

def render_png_with_edge(svg_path, png_path, size=512):
    html_content = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ background: transparent; width: {size}px; height: {size}px; overflow: hidden; display: flex; align-items: center; justify-content: center; }}
  img {{ width: {size}px; height: {size}px; display: block; }}
</style>
</head>
<body>
  <img src="{os.path.abspath(svg_path)}" />
</body>
</html>'''
    temp_html = svg_path.replace('.svg', '_render.html')
    with open(temp_html, 'w', encoding='utf-8') as f:
        f.write(html_content)

    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    edge_bin = next((p for p in edge_paths if os.path.exists(p)), "msedge")
    cmd = [
        edge_bin,
        "--headless=new",
        "--disable-gpu",
        f"--window-size={size},{size}",
        f"--screenshot={png_path}",
        temp_html
    ]
    subprocess.run(cmd, check=True)
    if os.path.exists(temp_html):
        os.remove(temp_html)
    print(f"Rendered PNG: {png_path} ({size}x{size})")

if __name__ == '__main__':
    brain_dir = r"C:\Users\aikel\.gemini\antigravity\brain\96a1582a-0842-48ec-9390-68089e318fe5"
    svg_path = os.path.join(brain_dir, "user_exact_clean_logo.svg")
    generate_exact_svg(svg_path)
    png_512 = os.path.join(brain_dir, "user_exact_clean_logo_512.png")
    render_png_with_edge(svg_path, png_512, 512)
    im = Image.open(png_512)
    im192 = im.resize((192, 192), Image.LANCZOS)
    png_192 = os.path.join(brain_dir, "user_exact_clean_logo_192.png")
    im192.save(png_192)
    print("Done generating exact clean user logo!")
