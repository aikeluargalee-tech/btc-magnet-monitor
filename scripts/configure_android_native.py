"""Copy custom Android MainActivity, MagnetNativeAdPlugin, and NativeAdView resources into Capacitor android/."""
import argparse
import os
import re
import shutil
import sys

APP_PACKAGE = "com.aikeluargalee.btcmagnet"
ADMOB_DEP_ARTIFACT = "com.google.android.gms:play-services-ads"
ADMOB_DEP_LINE = '    implementation "com.google.android.gms:play-services-ads:23.0.0"'

JAVA_FILES = (
    "MainActivity.java",
    "MagnetNativeAdPlugin.java",
)

LAYOUT_FILES = (
    "native_ad_card.xml",
)

DRAWABLE_FILES = (
    "native_ad_card_bg.xml",
    "native_ad_badge_bg.xml",
    "native_ad_cta_bg.xml",
)


def _copy_required_files(src_dir: str, dst_dir: str, filenames: tuple[str, ...]) -> list[str]:
    """Copy required files from src_dir to dst_dir and return destination paths."""
    os.makedirs(dst_dir, exist_ok=True)
    copied: list[str] = []
    for name in filenames:
        src_path = os.path.join(src_dir, name)
        if not os.path.isfile(src_path):
            raise FileNotFoundError(f"Required native Android source file missing: {src_path}")
        dst_path = os.path.join(dst_dir, name)
        shutil.copy2(src_path, dst_path)
        copied.append(dst_path)
    return copied


def ensure_admob_gradle_dependency(build_gradle_path: str) -> bool:
    """Idempotently add Play Services Ads dependency to android/app/build.gradle."""
    if not os.path.isfile(build_gradle_path):
        raise FileNotFoundError(f"Gradle build file not found: {build_gradle_path}")

    with open(build_gradle_path, "r", encoding="utf-8") as fh:
        content = fh.read()

    if ADMOB_DEP_ARTIFACT in content:
        return False

    pattern = re.compile(r"(dependencies\s*\{[^\r\n]*\r?\n)")
    match = pattern.search(content)
    if not match:
        raise RuntimeError(f"Could not find 'dependencies {{' block in {build_gradle_path}")

    updated = content[: match.end()] + ADMOB_DEP_LINE + "\n" + content[match.end() :]
    with open(build_gradle_path, "w", encoding="utf-8") as fh:
        fh.write(updated)
    return True


def apply_android_native(repo_root: str, android_dir: str | None = None) -> None:
    """Install custom Java plugin/MainActivity and NativeAd XML resources into android/app."""
    target_android = android_dir or os.path.join(repo_root, "android")
    if not os.path.isdir(target_android):
        raise FileNotFoundError(f"Capacitor android directory not found: {target_android}")

    native_root = os.path.join(repo_root, "android-native")
    java_dst = os.path.join(target_android, "app", "src", "main", "java", *APP_PACKAGE.split("."))
    res_dst = os.path.join(target_android, "app", "src", "main", "res")

    _copy_required_files(os.path.join(native_root, "java"), java_dst, JAVA_FILES)
    _copy_required_files(os.path.join(native_root, "res", "layout"), os.path.join(res_dst, "layout"), LAYOUT_FILES)
    _copy_required_files(
        os.path.join(native_root, "res", "drawable"), os.path.join(res_dst, "drawable"), DRAWABLE_FILES
    )

    gradle_path = os.path.join(target_android, "app", "build.gradle")
    gradle_changed = ensure_admob_gradle_dependency(gradle_path)
    status = "added Play Services Ads dependency" if gradle_changed else "Play Services Ads dependency already present"
    print(f"OK: applied custom native Android Java/res files into {target_android} ({status}).")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    parser.add_argument("--android-dir", default=None)
    args = parser.parse_args()

    target_android = args.android_dir or os.path.join(args.root, "android")
    if args.android_dir or os.path.isdir(target_android):
        apply_android_native(args.root, android_dir=target_android)
    else:
        print("android/ directory not present; nothing to apply.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
