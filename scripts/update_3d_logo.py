import os
import base64
import shutil

brain = r'C:\Users\aikel\.gemini\antigravity\brain\96a1582a-0842-48ec-9390-68089e318fe5'
repo = r'C:\Users\aikel\.gemini\antigravity\scratch\btc-magnet'

icon512_src = os.path.join(brain, 'user_3d_icon_512.png')
icon192_src = os.path.join(brain, 'user_3d_icon_192.png')

# Copy to repo and dist
for base_dir in [repo, os.path.join(repo, 'dist')]:
    shutil.copy2(icon512_src, os.path.join(base_dir, 'icon-512.png'))
    shutil.copy2(icon192_src, os.path.join(base_dir, 'icon-192.png'))
    os.makedirs(os.path.join(base_dir, 'assets'), exist_ok=True)
    shutil.copy2(icon512_src, os.path.join(base_dir, 'assets', 'logo.png'))

# Create SVG embedding the high-res 512 image
with open(icon512_src, 'rb') as f:
    b64_data = base64.b64encode(f.read()).decode('ascii')

svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <image href="data:image/png;base64,{b64_data}" x="0" y="0" width="512" height="512" />
</svg>'''

with open(os.path.join(repo, 'assets', 'logo.svg'), 'w', encoding='utf-8') as f:
    f.write(svg_content)
with open(os.path.join(repo, 'dist', 'assets', 'logo.svg'), 'w', encoding='utf-8') as f:
    f.write(svg_content)

print('Updated all logo and icon files across repo and dist!')
