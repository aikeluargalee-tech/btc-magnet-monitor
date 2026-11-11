import os
from PIL import Image, ImageDraw, ImageFont

def generate_svg(out_path):
    svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <defs>
    <!-- Dark background squircle -->
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#141419"/>
      <stop offset="100%" stop-color="#08080a"/>
    </linearGradient>
    
    <!-- Red pole (Left) -->
    <linearGradient id="redPole" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#f87171"/>
      <stop offset="50%" stop-color="#ef4444"/>
      <stop offset="100%" stop-color="#dc2626"/>
    </linearGradient>

    <!-- Cyan/Blue pole (Right) -->
    <linearGradient id="bluePole" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#38bdf8"/>
      <stop offset="50%" stop-color="#0ea5e9"/>
      <stop offset="100%" stop-color="#0284c7"/>
    </linearGradient>

    <!-- Neon Lime Green body -->
    <linearGradient id="greenBody" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#00e676"/>
      <stop offset="100%" stop-color="#00c853"/>
    </linearGradient>

    <!-- Bitcoin Gold -->
    <linearGradient id="goldGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#fffbeb"/>
      <stop offset="25%" stop-color="#fde047"/>
      <stop offset="70%" stop-color="#f59e0b"/>
      <stop offset="100%" stop-color="#d97706"/>
    </linearGradient>
    
    <filter id="goldGlow" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="8" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>

    <filter id="magnetGlow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="4" stdDeviation="12" flood-color="#00e676" flood-opacity="0.35"/>
    </filter>
  </defs>

  <!-- Squircle Outer Shell (One UI style) -->
  <rect x="8" y="8" width="496" height="496" rx="118" ry="118" fill="url(#bgGrad)" stroke="#27272a" stroke-width="3"/>

  <!-- Magnet Group with subtle glow -->
  <g filter="url(#magnetGlow)">
    <!-- Magnet Body: Green Left Vertical Arm -->
    <path d="M 96,164 L 168,164 L 168,280 L 96,280 Z" fill="url(#greenBody)"/>

    <!-- Magnet Body: Green Right Vertical Arm -->
    <path d="M 344,164 L 416,164 L 416,280 L 344,280 Z" fill="url(#greenBody)"/>

    <!-- Magnet Body: Bottom U-Curve Green (Outer r=160, Inner r=88, Center=(256, 280)) -->
    <path d="M 96,280 A 160,160 0 0,0 416,280 L 344,280 A 88,88 0 0,1 168,280 Z" fill="url(#greenBody)"/>

    <!-- Magnet Left Pole (Red) -->
    <path d="M 104,76 L 160,76 A 8,8 0 0,1 168,84 L 168,164 L 96,164 L 96,84 A 8,8 0 0,1 104,76 Z" fill="url(#redPole)"/>
    <!-- Divider Line -->
    <line x1="96" y1="164" x2="168" y2="164" stroke="#08080a" stroke-width="3"/>

    <!-- Magnet Right Pole (Cyan/Blue) -->
    <path d="M 352,76 L 408,76 A 8,8 0 0,1 416,84 L 416,164 L 344,164 L 344,84 A 8,8 0 0,1 352,76 Z" fill="url(#bluePole)"/>
    <!-- Divider Line -->
    <line x1="344" y1="164" x2="416" y2="164" stroke="#08080a" stroke-width="3"/>
  </g>

  <!-- Central Bitcoin B Symbol inside the hollow U -->
  <g filter="url(#goldGlow)">
    <!-- Decorative subtle circular gold aura behind ₿ -->
    <circle cx="256" cy="226" r="64" fill="#f59e0b" opacity="0.12"/>
    <text x="256" y="232" 
          font-family="'Segoe UI', -apple-system, BlinkMacSystemFont, Arial, sans-serif" 
          font-size="142" 
          font-weight="900" 
          text-anchor="middle" 
          dominant-baseline="central" 
          fill="url(#goldGrad)">₿</text>
  </g>
</svg>'''
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(svg_content)
    print(f"Generated SVG: {out_path}")

def render_png_with_edge(svg_path, png_path, size=512):
    import subprocess
    # Create temporary html to render SVG with msedge
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
    svg_brain = os.path.join(brain_dir, "magnet_b_logo.svg")
    generate_svg(svg_brain)
    png_512 = os.path.join(brain_dir, "magnet_b_logo_512.png")
    render_png_with_edge(svg_brain, png_512, 512)
    # Also resize to 192
    im512 = Image.open(png_512)
    im192 = im512.resize((192, 192), Image.LANCZOS)
    png_192 = os.path.join(brain_dir, "magnet_b_logo_192.png")
    im192.save(png_192)
    print("All logo files generated successfully!")
