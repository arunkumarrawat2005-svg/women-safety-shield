package org.womensafety.shield;

import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import android.os.VibrationEffect;
import android.os.Vibrator;
import android.webkit.JavascriptInterface;

public class AndroidBridge {

    private final MainActivity activity;
    private final Vibrator vibrator;
    private final SirenPlayer sirenPlayer;

    private static class UrlRunner implements Runnable {
        private final MainActivity activity;
        private final String url;

        public UrlRunner(MainActivity activity, String url) {
            this.activity = activity;
            this.url = url;
        }

        @Override
        public void run() {
            activity.setServerUrl(url);
        }
    }

    private static class DialogRunner implements Runnable {
        private final MainActivity activity;

        public DialogRunner(MainActivity activity) {
            this.activity = activity;
        }

        @Override
        public void run() {
            activity.showServerConfigDialog();
        }
    }

    private static class ReloadRunner implements Runnable {
        private final MainActivity activity;

        public ReloadRunner(MainActivity activity) {
            this.activity = activity;
        }

        @Override
        public void run() {
            activity.loadCurrentServer();
        }
    }

    public AndroidBridge(MainActivity activity, SirenPlayer sirenPlayer) {
        this.activity = activity;
        this.sirenPlayer = sirenPlayer;
        this.vibrator = (Vibrator) activity.getSystemService(Context.VIBRATOR_SERVICE);
    }

    @JavascriptInterface
    public boolean isNativeApp() {
        return true;
    }

    @JavascriptInterface
    public String getAppVersion() {
        return "2.5.0-Native-Shield";
    }

    @JavascriptInterface
    public String getServerUrl() {
        return activity.getServerUrl();
    }

    @JavascriptInterface
    public void setServerUrl(String url) {
        activity.runOnUiThread(new UrlRunner(activity, url));
    }

    @JavascriptInterface
    public void reloadServer() {
        activity.runOnUiThread(new ReloadRunner(activity));
    }

    @JavascriptInterface
    public void openServerConfigDialog() {
        activity.runOnUiThread(new DialogRunner(activity));
    }

    @JavascriptInterface
    public void vibrate(long milliseconds) {
        if (vibrator != null && vibrator.hasVibrator()) {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                vibrator.vibrate(VibrationEffect.createOneShot(milliseconds, VibrationEffect.DEFAULT_AMPLITUDE));
            } else {
                vibrator.vibrate(milliseconds);
            }
        }
    }

    @JavascriptInterface
    public void panicVibrate() {
        if (vibrator != null && vibrator.hasVibrator()) {
            long[] pattern = {0, 400, 150, 400, 150, 800};
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                vibrator.vibrate(VibrationEffect.createWaveform(pattern, -1));
            } else {
                vibrator.vibrate(pattern, -1);
            }
        }
    }

    @JavascriptInterface
    public void makeCall(String phoneNumber) {
        if (phoneNumber == null || phoneNumber.trim().isEmpty()) {
            phoneNumber = "112";
        }
        Intent intent = new Intent(Intent.ACTION_DIAL);
        intent.setData(Uri.parse("tel:" + phoneNumber.trim()));
        activity.startActivity(intent);
    }

    @JavascriptInterface
    public void playSiren() {
        if (sirenPlayer != null) {
            sirenPlayer.play();
        }
    }

    @JavascriptInterface
    public void stopSiren() {
        if (sirenPlayer != null) {
            sirenPlayer.stop();
        }
    }

    @JavascriptInterface
    public void showToast(String message) {
        activity.showToast(message);
    }

    @JavascriptInterface
    public void triggerNativeEmergency(double lat, double lng) {
        panicVibrate();
        playSiren();
        showToast("DISTRESS TRANSMITTED VIA SHIELD APK (Lat: " + lat + ", Lng: " + lng + ")");
    }
}
