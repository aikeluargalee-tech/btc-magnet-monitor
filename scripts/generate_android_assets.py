"""Generate web, PWA, splash, and Android launcher icons from the master full-size logo.

Usage:
  python scripts/generate_android_assets.py            # Applies Android res/ if android/ exists
  python scripts/generate_android_assets.py --sync-web # Also refreshes root/assets web & PWA icons
"""
import argparse
import base64
import io
import os
import sys

try:
    from PIL import Image, ImageDraw
except ImportError as exc:
    Image = None  # type: ignore
    ImageDraw = None  # type: ignore
    _PIL_ERROR = exc
else:
    _PIL_ERROR = None


MASTER_ICON_REL = os.path.join("branding", "app-icon-fullsize.png")
ICON_BG_HEX = "#1C2029"
ICON_BG_RGBA = (28, 32, 41, 255)
SPLASH_BG_RGBA = (9, 9, 11, 255)

MIPMAP_DENSITIES = {
    "mdpi": (48, 108),
    "hdpi": (72, 162),
    "xhdpi": (96, 216),
    "xxhdpi": (144, 324),
    "xxxhdpi": (192, 432),
}

SPLASH_SPECS = {
    "drawable": (480, 320),
    "drawable-port-mdpi": (320, 480),
    "drawable-port-hdpi": (480, 800),
    "drawable-port-xhdpi": (720, 1280),
    "drawable-port-xxhdpi": (960, 1600),
    "drawable-port-xxxhdpi": (1280, 1920),
    "drawable-land-mdpi": (480, 320),
    "drawable-land-hdpi": (800, 480),
    "drawable-land-xhdpi": (1280, 720),
    "drawable-land-xxhdpi": (1600, 960),
    "drawable-land-xxxhdpi": (1920, 1280),
}

STALE_CAPACITOR_DRAWABLES = (
    os.path.join("drawable-anydpi-v24", "ic_launcher_foreground.xml"),
    os.path.join("drawable-anydpi-v24", "$ic_launcher_foreground__0.xml"),
    os.path.join("drawable", "ic_launcher_background.xml"),
)

BACKGROUND_XML = f"""<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="app_icon_background">{ICON_BG_HEX}</color>
</resources>
"""

ADAPTIVE_ICON_XML = """<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/app_icon_background"/>
    <foreground android:drawable="@mipmap/ic_launcher_foreground"/>
</adaptive-icon>
"""


def _require_pil() -> None:
    if Image is None:
        raise RuntimeError(f"Pillow is required for icon generation: {_PIL_ERROR}")


def _feathered_foreground(src: "Image.Image", canvas_px: int, scale: float = 0.80) -> "Image.Image":
    """Place the full-size icon centered inside canvas_px with softly faded outer edge onto transparent."""
    canvas = Image.new("RGBA", (canvas_px, canvas_px), (0, 0, 0, 0))
    inner = max(16, int(round(canvas_px * scale)))
    resized = src.resize((inner, inner), Image.Resampling.LANCZOS)

    alpha = Image.new("L", (inner, inner), 255)
    fade = max(4, int(round(inner * 0.12)))
    px = alpha.load()
    for y in range(inner):
        dy = min(y, inner - 1 - y)
        for x in range(inner):
            d = min(x, inner - 1 - x, dy)
            if d < fade:
                px[x, y] = int(255 * (d / fade))

    offset = (canvas_px - inner) // 2
    canvas.paste(resized, (offset, offset), alpha)
    return canvas


def _composite_adaptive_square(src: "Image.Image", size_px: int, scale: float = 0.80) -> "Image.Image":
    """Composite adaptive foreground cleanly over #1C2029 background (used for maskable/round icons)."""
    canvas = Image.new("RGBA", (size_px, size_px), ICON_BG_RGBA)
    fg = _feathered_foreground(src, size_px, scale=scale)
    return Image.alpha_composite(canvas, fg)


def _round_icon(src: "Image.Image", size_px: int) -> "Image.Image":
    """Create an anti-aliased circular launcher icon safe against clipping."""
    hi = size_px * 4
    # Fill central 72/108 viewport so the magnet matches adaptive circle proportion
    ad_hi = int(round(hi * 1.5))
    comp = _composite_adaptive_square(src, ad_hi, scale=0.80)
    crop = (ad_hi - hi) // 2
    view = comp.crop((crop, crop, crop + hi, crop + hi))

    mask = Image.new("L", (hi, hi), 0)
    ImageDraw.Draw(mask).ellipse((4, 4, hi - 5, hi - 5), fill=255)
    out = Image.new("RGBA", (hi, hi), (0, 0, 0, 0))
    out.paste(view, (0, 0), mask)
    return out.resize((size_px, size_px), Image.Resampling.LANCZOS)


def _legacy_square_icon(src: "Image.Image", size_px: int) -> "Image.Image":
    """Full-size launcher icon for legacy Android densities & store previews."""
    return src.resize((size_px, size_px), Image.Resampling.LANCZOS)


def _splash_image(src: "Image.Image", width: int, height: int) -> "Image.Image":
    """Dark #09090b splash screen with centered rounded full-size logo badge."""
    canvas = Image.new("RGBA", (width, height), SPLASH_BG_RGBA)
    badge_sz = max(96, int(round(min(width, height) * 0.34)))
    badge = src.resize((badge_sz, badge_sz), Image.Resampling.LANCZOS)

    mask = Image.new("L", (badge_sz, badge_sz), 0)
    radius = max(16, int(round(badge_sz * 0.22)))
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, badge_sz - 1, badge_sz - 1), radius=radius, fill=255)

    x = (width - badge_sz) // 2
    y = (height - badge_sz) // 2
    canvas.paste(badge, (x, y), mask)
    return canvas.convert("RGB")


def sync_web_icons(root_dir: str) -> None:
    """Update root/assets web, header, and PWA icons from the full-size 1024x1024 master PNG."""
    _require_pil()
    master_path = os.path.join(root_dir, MASTER_ICON_REL)
    src = Image.open(master_path).convert("RGBA")

    png_512 = _legacy_square_icon(src, 512)
    png_192 = _legacy_square_icon(src, 192)
    maskable_512 = _composite_adaptive_square(src, 768, scale=0.80).crop((128, 128, 640, 640))

    png_512.save(os.path.join(root_dir, "icon-512.png"), optimize=True)
    png_192.save(os.path.join(root_dir, "icon-192.png"), optimize=True)
    maskable_512.save(os.path.join(root_dir, "icon-maskable-512.png"), optimize=True)

    assets_dir = os.path.join(root_dir, "assets")
    os.makedirs(assets_dir, exist_ok=True)
    png_512.save(os.path.join(assets_dir, "app-logo.png"), optimize=True)
    png_512.save(os.path.join(assets_dir, "logo.png"), optimize=True)

    buf = io.BytesIO()
    png_512.save(buf, format="PNG", optimize=True)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">\n'
        f'  <image href="data:image/png;base64,{b64}" x="0" y="0" width="512" height="512" />\n'
        '</svg>\n'
    )
    with open(os.path.join(assets_dir, "logo.svg"), "w", encoding="utf-8") as fh:
        fh.write(svg)
    print("OK: synced web, header, and PWA icons from full-size 1024x1024 logo.")


def apply_android_resources(root_dir: str, res_dir: str | None = None) -> None:
    """Replace Capacitor default launcher & splash resources inside android/app/src/main/res."""
    _require_pil()
    master_path = os.path.join(root_dir, MASTER_ICON_REL)
    if not os.path.exists(master_path):
        raise FileNotFoundError(f"Master icon not found: {master_path}")

    target_res = res_dir or os.path.join(root_dir, "android", "app", "src", "main", "res")
    src = Image.open(master_path).convert("RGBA")

    # Remove default Capacitor vector X drawables so Android 8+ adaptive mipmaps take effect cleanly
    for rel in STALE_CAPACITOR_DRAWABLES:
        stale = os.path.join(target_res, rel)
        if os.path.exists(stale):
            os.remove(stale)

    values_dir = os.path.join(target_res, "values")
    os.makedirs(values_dir, exist_ok=True)
    with open(os.path.join(values_dir, "ic_launcher_background.xml"), "w", encoding="utf-8") as fh:
        fh.write(BACKGROUND_XML)

    anydpi_dir = os.path.join(target_res, "mipmap-anydpi-v26")
    os.makedirs(anydpi_dir, exist_ok=True)
    with open(os.path.join(anydpi_dir, "ic_launcher.xml"), "w", encoding="utf-8") as fh:
        fh.write(ADAPTIVE_ICON_XML)
    with open(os.path.join(anydpi_dir, "ic_launcher_round.xml"), "w", encoding="utf-8") as fh:
        fh.write(ADAPTIVE_ICON_XML)

    for density, (icon_px, fg_px) in MIPMAP_DENSITIES.items():
        mdir = os.path.join(target_res, f"mipmap-{density}")
        os.makedirs(mdir, exist_ok=True)
        _legacy_square_icon(src, icon_px).save(os.path.join(mdir, "ic_launcher.png"), optimize=True)
        _round_icon(src, icon_px).save(os.path.join(mdir, "ic_launcher_round.png"), optimize=True)
        _feathered_foreground(src, fg_px, scale=0.80).save(
            os.path.join(mdir, "ic_launcher_foreground.png"), optimize=True
        )

    for folder, (w, h) in SPLASH_SPECS.items():
        ddir = os.path.join(target_res, folder)
        os.makedirs(ddir, exist_ok=True)
        _splash_image(src, w, h).save(os.path.join(ddir, "splash.png"), optimize=True)

    print(f"OK: generated Android adaptive/legacy launcher icons and splash screens into {target_res}.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    parser.add_argument("--res-dir", default=None)
    parser.add_argument("--sync-web", action="store_true")
    args = parser.parse_args()

    if args.sync_web:
        sync_web_icons(args.root)
    android_dir = args.res_dir or os.path.join(args.root, "android", "app", "src", "main", "res")
    if args.res_dir or os.path.exists(os.path.join(args.root, "android")):
        apply_android_resources(args.root, res_dir=android_dir)
    elif not args.sync_web:
        print("android/ directory not present; nothing to apply.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
