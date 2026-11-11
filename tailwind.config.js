/**
 * Used ONLY by the Android app build (see .github/workflows/build-android-apk.yml).
 * Scans the Python generators too, so classes that only appear for OTHER market regimes
 * (e.g. bearish/bullish colour variants) are still included in the bundled CSS.
 */
module.exports = {
  content: ['./web/*.py', './engine/*.py', './dist/*.html'],
  theme: { extend: {} },
  plugins: [],
};
