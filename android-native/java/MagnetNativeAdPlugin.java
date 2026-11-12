package com.aikeluargalee.btcmagnet;

import android.app.Activity;
import android.content.Context;
import android.graphics.Rect;
import android.view.Gravity;
import android.view.LayoutInflater;
import android.view.MotionEvent;
import android.view.VelocityTracker;
import android.view.View;
import android.view.ViewConfiguration;
import android.view.ViewGroup;
import android.view.ViewTreeObserver;
import android.webkit.WebView;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.TextView;
import androidx.annotation.NonNull;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import com.google.android.gms.ads.AdListener;
import com.google.android.gms.ads.AdLoader;
import com.google.android.gms.ads.AdRequest;
import com.google.android.gms.ads.LoadAdError;
import com.google.android.gms.ads.VideoOptions;
import com.google.android.gms.ads.nativead.MediaView;
import com.google.android.gms.ads.nativead.NativeAd;
import com.google.android.gms.ads.nativead.NativeAdOptions;
import com.google.android.gms.ads.nativead.NativeAdView;

@CapacitorPlugin(name = "MagnetNativeAd")
public class MagnetNativeAdPlugin extends Plugin {

    private static final String TEST_NATIVE_AD_UNIT_ID = "ca-app-pub-3940256099942544/2247696110";

    private FrameLayout adViewportHost;
    private AdScrollOverlayLayout adWrapper;
    private NativeAdView nativeAdView;
    private NativeAd currentNativeAd;

    private ViewGroup rootContainer;
    private WebView attachedWebView;
    private ViewTreeObserver.OnScrollChangedListener scrollListener;
    private View.OnLayoutChangeListener rootLayoutListener;

    private float anchorLeftCss = 0f;
    private float anchorDocTopCss = 0f;
    private float anchorWidthCss = 0f;
    private boolean hasAnchorRect = false;
    private boolean slotVisible = false;
    private int currentMeasuredWidthPx = 0;
    private int currentMeasuredHeightPx = 0;
    private int clipBottomPx = Integer.MAX_VALUE;

    @PluginMethod
    public void loadAndAttach(final PluginCall call) {
        final String requestedId = call.getString("adUnitId");
        final String adUnitId = (requestedId != null && !requestedId.trim().isEmpty())
            ? requestedId.trim()
            : TEST_NATIVE_AD_UNIT_ID;
        final float initialWidthCss = call.getFloat("widthCss", 0f);

        final Activity activity = getActivity();
        if (activity == null || activity.isFinishing() || activity.isDestroyed()) {
            call.reject("Activity unavailable");
            return;
        }

        activity.runOnUiThread(() -> {
            ensureHostAttached();
            if (initialWidthCss > 0f) {
                anchorWidthCss = initialWidthCss;
            }

            NativeAdOptions adOptions = new NativeAdOptions.Builder()
                .setVideoOptions(new VideoOptions.Builder().setStartMuted(true).build())
                .build();

            AdLoader adLoader = new AdLoader.Builder(activity, adUnitId)
                .forNativeAd(nativeAd -> activity.runOnUiThread(() -> {
                    if (activity.isFinishing() || activity.isDestroyed()) {
                        nativeAd.destroy();
                        return;
                    }
                    renderLoadedNativeAd(nativeAd, call);
                }))
                .withNativeAdOptions(adOptions)
                .withAdListener(new AdListener() {
                    @Override
                    public void onAdFailedToLoad(@NonNull LoadAdError loadAdError) {
                        JSObject err = new JSObject();
                        err.put("code", loadAdError.getCode());
                        err.put("message", loadAdError.getMessage());
                        notifyListeners("nativeAdFailed", err);
                        call.reject("Native ad failed: " + loadAdError.getMessage());
                    }

                    @Override
                    public void onAdClicked() {
                        notifyListeners("nativeAdClicked", new JSObject());
                    }

                    @Override
                    public void onAdImpression() {
                        notifyListeners("nativeAdImpression", new JSObject());
                    }
                })
                .build();

            adLoader.loadAd(new AdRequest.Builder().build());
        });
    }

    @PluginMethod
    public void updateRect(final PluginCall call) {
        final float leftCss = call.getFloat("leftCss", 0f);
        final float docTopCss = call.getFloat("docTopCss", 0f);
        final float widthCss = call.getFloat("widthCss", 0f);

        final Activity activity = getActivity();
        if (activity == null) {
            call.resolve();
            return;
        }

        activity.runOnUiThread(() -> {
            anchorLeftCss = leftCss;
            anchorDocTopCss = docTopCss;
            hasAnchorRect = true;

            if (widthCss > 0f && Math.abs(widthCss - anchorWidthCss) > 0.5f) {
                anchorWidthCss = widthCss;
                if (adWrapper != null && nativeAdView != null) {
                    double heightCss = measureAndApplyWrapperSize();
                    JSObject resized = new JSObject();
                    resized.put("heightCss", heightCss);
                    notifyListeners("nativeAdLoaded", resized);
                }
            }

            repositionCard();
            call.resolve();
        });
    }

    @PluginMethod
    public void setVisible(final PluginCall call) {
        final boolean visible = Boolean.TRUE.equals(call.getBoolean("visible", false));
        final Activity activity = getActivity();
        if (activity == null) {
            call.resolve();
            return;
        }
        activity.runOnUiThread(() -> {
            slotVisible = visible;
            repositionCard();
            call.resolve();
        });
    }

    @Override
    protected void handleOnDestroy() {
        Activity activity = getActivity();
        if (activity != null) {
            activity.runOnUiThread(this::cleanupViews);
        } else {
            cleanupViews();
        }
        super.handleOnDestroy();
    }

    private void cleanupViews() {
        if (attachedWebView != null && scrollListener != null) {
            ViewTreeObserver vto = attachedWebView.getViewTreeObserver();
            if (vto.isAlive()) {
                vto.removeOnScrollChangedListener(scrollListener);
            }
        }
        scrollListener = null;

        if (rootContainer != null && rootLayoutListener != null) {
            rootContainer.removeOnLayoutChangeListener(rootLayoutListener);
        }
        rootLayoutListener = null;

        if (currentNativeAd != null) {
            currentNativeAd.destroy();
            currentNativeAd = null;
        }
        if (adViewportHost != null && adViewportHost.getParent() instanceof ViewGroup) {
            ((ViewGroup) adViewportHost.getParent()).removeView(adViewportHost);
        }
        adWrapper = null;
        nativeAdView = null;
        adViewportHost = null;
    }

    private void ensureHostAttached() {
        Activity activity = getActivity();
        if (activity == null || getBridge() == null) {
            return;
        }

        if (rootContainer == null) {
            View content = activity.findViewById(android.R.id.content);
            if (content instanceof ViewGroup && ((ViewGroup) content).getChildCount() > 0) {
                View first = ((ViewGroup) content).getChildAt(0);
                if (first instanceof ViewGroup) {
                    rootContainer = (ViewGroup) first;
                }
            }
        }
        if (rootContainer == null) {
            return;
        }

        if (adViewportHost == null) {
            adViewportHost = new FrameLayout(activity);
            adViewportHost.setClipChildren(true);
            adViewportHost.setClipToPadding(true);
            ViewGroup.LayoutParams lp = new ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT
            );
            // Insert immediately above WebView (index 0) and below any bottom AdMob banner added later.
            int insertIndex = Math.min(1, rootContainer.getChildCount());
            rootContainer.addView(adViewportHost, insertIndex, lp);
        }

        if (rootLayoutListener == null) {
            rootLayoutListener = (v, l, t, r, b, ol, ot, or, ob) -> {
                updateViewportClipBounds();
                repositionCard();
            };
            rootContainer.addOnLayoutChangeListener(rootLayoutListener);
        }

        WebView webView = getBridge().getWebView();
        if (webView != null && attachedWebView != webView) {
            attachedWebView = webView;
            scrollListener = this::repositionCard;
            attachedWebView.getViewTreeObserver().addOnScrollChangedListener(scrollListener);
        }
        updateViewportClipBounds();
    }

    private void renderLoadedNativeAd(NativeAd nativeAd, PluginCall call) {
        Activity activity = getActivity();
        if (activity == null || adViewportHost == null) {
            nativeAd.destroy();
            call.reject("Ad host unavailable");
            return;
        }

        if (currentNativeAd != null) {
            currentNativeAd.destroy();
        }
        currentNativeAd = nativeAd;

        if (adWrapper != null) {
            adViewportHost.removeView(adWrapper);
            adWrapper = null;
            nativeAdView = null;
        }

        LayoutInflater inflater = LayoutInflater.from(activity);
        NativeAdView adView = (NativeAdView) inflater.inflate(R.layout.native_ad_card, adViewportHost, false);

        TextView headlineView = adView.findViewById(R.id.ad_headline);
        TextView advertiserView = adView.findViewById(R.id.ad_advertiser);
        TextView bodyView = adView.findViewById(R.id.ad_body);
        ImageView iconView = adView.findViewById(R.id.ad_icon);
        MediaView mediaView = adView.findViewById(R.id.ad_media);
        Button ctaView = adView.findViewById(R.id.ad_call_to_action);

        adView.setHeadlineView(headlineView);
        adView.setAdvertiserView(advertiserView);
        adView.setBodyView(bodyView);
        adView.setIconView(iconView);
        adView.setMediaView(mediaView);
        adView.setCallToActionView(ctaView);

        headlineView.setText(nativeAd.getHeadline() != null ? nativeAd.getHeadline() : "Sponsored");

        if (nativeAd.getAdvertiser() != null && !nativeAd.getAdvertiser().trim().isEmpty()) {
            advertiserView.setText(nativeAd.getAdvertiser());
            advertiserView.setVisibility(View.VISIBLE);
        } else {
            advertiserView.setText("Sponsored");
            advertiserView.setVisibility(View.VISIBLE);
        }

        if (nativeAd.getBody() != null && !nativeAd.getBody().trim().isEmpty()) {
            bodyView.setText(nativeAd.getBody());
            bodyView.setVisibility(View.VISIBLE);
        } else {
            bodyView.setVisibility(View.GONE);
        }

        if (nativeAd.getIcon() != null) {
            iconView.setImageDrawable(nativeAd.getIcon().getDrawable());
            iconView.setVisibility(View.VISIBLE);
        } else {
            iconView.setVisibility(View.GONE);
        }

        if (nativeAd.getMediaContent() != null) {
            mediaView.setMediaContent(nativeAd.getMediaContent());
            mediaView.setVisibility(View.VISIBLE);
        } else {
            mediaView.setVisibility(View.GONE);
        }

        if (nativeAd.getCallToAction() != null && !nativeAd.getCallToAction().trim().isEmpty()) {
            ctaView.setText(nativeAd.getCallToAction());
            ctaView.setVisibility(View.VISIBLE);
        } else {
            ctaView.setVisibility(View.GONE);
        }

        adView.setNativeAd(nativeAd);
        nativeAdView = adView;

        adWrapper = new AdScrollOverlayLayout(activity);
        adWrapper.addView(
            adView,
            new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
            )
        );
        adWrapper.setVisibility(View.INVISIBLE);

        FrameLayout.LayoutParams wrapperParams = new FrameLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,
            ViewGroup.LayoutParams.WRAP_CONTENT,
            Gravity.TOP | Gravity.LEFT
        );
        adViewportHost.addView(adWrapper, wrapperParams);

        double heightCss = measureAndApplyWrapperSize();
        slotVisible = true;
        repositionCard();

        JSObject result = new JSObject();
        result.put("heightCss", heightCss);
        result.put("headline", nativeAd.getHeadline());
        notifyListeners("nativeAdLoaded", result);
        call.resolve(result);
    }

    private double measureAndApplyWrapperSize() {
        if (adWrapper == null || rootContainer == null) {
            return 0.0;
        }
        float scale = getWebViewScale();
        int fallbackWidth = Math.max(200, rootContainer.getWidth() - Math.round(16f * scale));
        int targetWidthPx = anchorWidthCss > 0f
            ? Math.max(120, Math.round(anchorWidthCss * scale))
            : fallbackWidth;

        adWrapper.measure(
            View.MeasureSpec.makeMeasureSpec(targetWidthPx, View.MeasureSpec.EXACTLY),
            View.MeasureSpec.makeMeasureSpec(0, View.MeasureSpec.UNSPECIFIED)
        );
        int measuredHeightPx = Math.max(1, adWrapper.getMeasuredHeight());

        ViewGroup.LayoutParams lp = adWrapper.getLayoutParams();
        if (lp.width != targetWidthPx || lp.height != measuredHeightPx) {
            lp.width = targetWidthPx;
            lp.height = measuredHeightPx;
            adWrapper.setLayoutParams(lp);
        }
        currentMeasuredWidthPx = targetWidthPx;
        currentMeasuredHeightPx = measuredHeightPx;
        return measuredHeightPx / (double) scale;
    }

    private void updateViewportClipBounds() {
        if (adViewportHost == null || rootContainer == null) {
            return;
        }
        int hostWidth = adViewportHost.getWidth();
        int hostHeight = adViewportHost.getHeight();
        if (hostWidth <= 0 || hostHeight <= 0) {
            clipBottomPx = Integer.MAX_VALUE;
            return;
        }
        int bottomLimit = hostHeight;
        for (int i = 0; i < rootContainer.getChildCount(); i++) {
            View child = rootContainer.getChildAt(i);
            if (child == attachedWebView || child == adViewportHost) {
                continue;
            }
            if (child.getVisibility() == View.VISIBLE && child.getHeight() > 0) {
                // Any bottom-docked AdMob banner container sets a crisp ceiling above itself.
                if (child.getTop() > hostHeight / 2) {
                    bottomLimit = Math.min(bottomLimit, child.getTop());
                }
            }
        }
        clipBottomPx = Math.max(0, bottomLimit);
        adViewportHost.setClipBounds(new Rect(0, 0, hostWidth, clipBottomPx));
    }

    private void repositionCard() {
        if (adWrapper == null || attachedWebView == null) {
            return;
        }
        if (!slotVisible || !hasAnchorRect || currentMeasuredWidthPx <= 0 || currentMeasuredHeightPx <= 0) {
            adWrapper.setVisibility(View.INVISIBLE);
            return;
        }
        float scale = getWebViewScale();
        float xPx = (anchorLeftCss * scale) - attachedWebView.getScrollX();
        float yPx = (anchorDocTopCss * scale) - attachedWebView.getScrollY();

        adWrapper.setTranslationX(xPx);
        adWrapper.setTranslationY(yPx);

        boolean visibleInViewport = (yPx + currentMeasuredHeightPx) > 0f && yPx < clipBottomPx;
        adWrapper.setVisibility(visibleInViewport ? View.VISIBLE : View.INVISIBLE);
    }

    private float getWebViewScale() {
        if (attachedWebView != null) {
            float s = attachedWebView.getScale();
            if (s > 0f) {
                return s;
            }
        }
        Activity activity = getActivity();
        if (activity != null) {
            return activity.getResources().getDisplayMetrics().density;
        }
        return 1f;
    }

    /**
     * Allows normal taps to reach NativeAdView CTA/AdChoices while forwarding vertical drags
     * straight to the sibling Capacitor WebView so scrolling over the inline ad stays fluid.
     */
    private final class AdScrollOverlayLayout extends FrameLayout {

        private final int touchSlop;
        private float startRawY;
        private float lastRawY;
        private boolean dragging;
        private VelocityTracker velocityTracker;

        AdScrollOverlayLayout(Context context) {
            super(context);
            touchSlop = ViewConfiguration.get(context).getScaledTouchSlop();
        }

        @Override
        public boolean onInterceptTouchEvent(MotionEvent ev) {
            switch (ev.getActionMasked()) {
                case MotionEvent.ACTION_DOWN:
                    startRawY = ev.getRawY();
                    lastRawY = startRawY;
                    dragging = false;
                    recycleVelocityTracker();
                    velocityTracker = VelocityTracker.obtain();
                    velocityTracker.addMovement(ev);
                    return false;
                case MotionEvent.ACTION_MOVE:
                    if (velocityTracker != null) {
                        velocityTracker.addMovement(ev);
                    }
                    if (Math.abs(ev.getRawY() - startRawY) > touchSlop) {
                        dragging = true;
                        lastRawY = ev.getRawY();
                        return true;
                    }
                    return false;
                case MotionEvent.ACTION_UP:
                case MotionEvent.ACTION_CANCEL:
                    dragging = false;
                    recycleVelocityTracker();
                    return false;
                default:
                    return false;
            }
        }

        @Override
        public boolean onTouchEvent(MotionEvent ev) {
            if (attachedWebView == null) {
                return false;
            }
            if (velocityTracker != null) {
                velocityTracker.addMovement(ev);
            }
            switch (ev.getActionMasked()) {
                case MotionEvent.ACTION_MOVE:
                    float currentY = ev.getRawY();
                    int dy = Math.round(lastRawY - currentY);
                    lastRawY = currentY;
                    if (dy != 0) {
                        int maxScrollY = Math.max(
                            0,
                            (int) Math.ceil(attachedWebView.getContentHeight() * getWebViewScale()) - attachedWebView.getHeight()
                        );
                        int nextY = Math.max(0, Math.min(maxScrollY, attachedWebView.getScrollY() + dy));
                        attachedWebView.scrollTo(attachedWebView.getScrollX(), nextY);
                        repositionCard();
                    }
                    return true;
                case MotionEvent.ACTION_UP:
                    if (dragging && velocityTracker != null) {
                        velocityTracker.computeCurrentVelocity(1000);
                        int vy = Math.round(-velocityTracker.getYVelocity());
                        if (Math.abs(vy) > 150) {
                            attachedWebView.flingScroll(0, vy);
                        }
                    }
                    dragging = false;
                    recycleVelocityTracker();
                    return true;
                case MotionEvent.ACTION_CANCEL:
                    dragging = false;
                    recycleVelocityTracker();
                    return true;
                default:
                    return dragging;
            }
        }

        private void recycleVelocityTracker() {
            if (velocityTracker != null) {
                velocityTracker.recycle();
                velocityTracker = null;
            }
        }
    }
}
