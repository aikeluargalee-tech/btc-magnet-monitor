import os
import base64
import shutil

brain = r'C:\Users\aikel\.gemini\antigravity\brain\96a1582a-0842-48ec-9390-68089e318fe5'
repo = r'C:\Users\aikel\.gemini\antigravity\scratch\btc-magnet'

logo_trans_src = os.path.join(brain, 'app_logo_transparent_512.png')
icon512_src = os.path.join(brain, 'app_icon_512.png')
icon192_src = os.path.join(brain, 'app_icon_192.png')
maskable512_src = os.path.join(brain, 'app_icon_maskable_512.png')

# Copy to repo and dist
for base_dir in [repo, os.path.join(repo, 'dist')]:
    os.makedirs(os.path.join(base_dir, 'assets'), exist_ok=True)
    shutil.copy2(logo_trans_src, os.path.join(base_dir, 'assets', 'app-logo.png'))
    shutil.copy2(logo_trans_src, os.path.join(base_dir, 'assets', 'logo.png'))
    shutil.copy2(icon512_src, os.path.join(base_dir, 'icon-512.png'))
    shutil.copy2(icon192_src, os.path.join(base_dir, 'icon-192.png'))
    if os.path.exists(maskable512_src):
        shutil.copy2(maskable512_src, os.path.join(base_dir, 'icon-maskable-512.png'))

# Create SVG embedding the clean 512 transparent artwork
with open(logo_trans_src, 'rb') as f:
    b64_data = base64.b64encode(f.read()).decode('ascii')

svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <image href="data:image/png;base64,{b64_data}" x="0" y="0" width="512" height="512" />
</svg>'''

with open(os.path.join(repo, 'assets', 'logo.svg'), 'w', encoding='utf-8') as f:
    f.write(svg_content)
with open(os.path.join(repo, 'dist', 'assets', 'logo.svg'), 'w', encoding='utf-8') as f:
    f.write(svg_content)

print('Generated and deployed all official 3D logo and maskable icon files successfully!')
