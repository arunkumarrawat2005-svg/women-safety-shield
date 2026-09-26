package org.womensafety.shield;

import android.Manifest;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.hardware.Sensor;
import android.hardware.SensorManager;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.view.View;
import android.webkit.GeolocationPermissions;
import android.webkit.PermissionRequest;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.EditText;
import android.widget.ImageButton;
import android.widget.ProgressBar;
import android.widget.Toast;

public class MainActivity extends Activity {

    private static final String PREFS_NAME = "WomenSafetyShieldPrefs_v3";
    private static final String PREF_SERVER_URL = "server_url";
    public static final String DEFAULT_URL = "file:///android_asset/www/index.html";
    private static final String LAN_SERVER_URL = "http://192.168.4.31:8000/";
    private static final int PERMISSION_REQUEST_CODE = 1001;
    private static final int FILE_CHOOSER_REQUEST_CODE = 1002;

    private WebView webView;
    private ProgressBar progressBar;
    private ImageButton btnSettings;
    private SensorManager sensorManager;
    private Sensor accelerometer;
    private HardwareShakeDetector shakeDetector;
    private SirenPlayer sirenPlayer;
    private ValueCallback<Uri[]> uploadMessage;
    private long backPressedTime = 0;

    private static class LanProbeRunner implements Runnable {
        private final MainActivity activity;
        private final String targetUrl;

        public LanProbeRunner(MainActivity activity, String targetUrl) {
            this.activity = activity;
            this.targetUrl = targetUrl;
        }

        @Override
        public void run() {
            if (activity.webView != null) {
                activity.webView.loadUrl(targetUrl);
                Toast.makeText(activity, "Connected to Live Server (" + targetUrl + ")", Toast.LENGTH_SHORT).show();
            }
        }
    }

    private static class LanProbeThread extends Thread {
        private final MainActivity activity;

        public LanProbeThread(MainActivity activity) {
            this.activity = activity;
        }

        @Override
        public void run() {
            try {
                java.net.URL url = new java.net.URL(LAN_SERVER_URL);
                java.net.HttpURLConnection conn = (java.net.HttpURLConnection) url.openConnection();
                conn.setConnectTimeout(800);
                conn.setReadTimeout(800);
                conn.setRequestMethod("HEAD");
                int code = conn.getResponseCode();
                if (code >= 200 && code < 400) {
                    activity.runOnUiThread(new LanProbeRunner(activity, LAN_SERVER_URL));
                }
                conn.disconnect();
            } catch (Exception ignored) {
                // Local server not reachable on current network; remain on bundled offline assets
            }
        }
    }

    private static class ToastRunner implements Runnable {
        private final Context context;
        private final String message;

        public ToastRunner(Context context, String message) {
            this.context = context;
            this.message = message;
        }

        @Override
        public void run() {
            Toast.makeText(context, message, Toast.LENGTH_SHORT).show();
        }
    }

    private static class ShakeListenerImpl implements HardwareShakeDetector.OnShakeListener {
        private final MainActivity activity;

        public ShakeListenerImpl(MainActivity activity) {
            this.activity = activity;
        }

        @Override
        public void onShake(int count) {
            if (count >= 2) {
                activity.handlePanicShake();
            }
        }
    }

    private static class SettingsClickListener implements View.OnClickListener {
        private final MainActivity activity;

        public SettingsClickListener(MainActivity activity) {
            this.activity = activity;
        }

        @Override
        public void onClick(View v) {
            activity.showServerConfigDialog();
        }
    }

    private static class ChromeClientImpl extends WebChromeClient {
        private final MainActivity activity;

        public ChromeClientImpl(MainActivity activity) {
            this.activity = activity;
        }

        @Override
        public void onProgressChanged(WebView view, int newProgress) {
            if (activity.progressBar != null) {
                if (newProgress < 100) {
                    activity.progressBar.setVisibility(View.VISIBLE);
                    activity.progressBar.setProgress(newProgress);
                } else {
                    activity.progressBar.setVisibility(View.GONE);
                }
            }
        }

        @Override
        public void onGeolocationPermissionsShowPrompt(String origin, GeolocationPermissions.Callback callback) {
            callback.invoke(origin, true, false);
        }

        @Override
        public void onPermissionRequest(PermissionRequest request) {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
                request.grant(request.getResources());
            }
        }

        @Override
        public boolean onShowFileChooser(WebView webView, ValueCallback<Uri[]> filePathCallback, FileChooserParams fileChooserParams) {
            if (activity.uploadMessage != null) {
                activity.uploadMessage.onReceiveValue(null);
            }
            activity.uploadMessage = filePathCallback;

            Intent intent = null;
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
                intent = fileChooserParams.createIntent();
            } else {
                intent = new Intent(Intent.ACTION_GET_CONTENT);
                intent.addCategory(Intent.CATEGORY_OPENABLE);
                intent.setType("*/*");
            }
            try {
                activity.startActivityForResult(intent, FILE_CHOOSER_REQUEST_CODE);
            } catch (Exception e) {
                activity.uploadMessage = null;
                return false;
            }
            return true;
        }
    }

    private static class WebClientImpl extends WebViewClient {
        private final MainActivity activity;

        public WebClientImpl(MainActivity activity) {
            this.activity = activity;
        }

        @Override
        public boolean shouldOverrideUrlLoading(WebView view, String url) {
            if (url.startsWith("tel:")) {
                Intent intent = new Intent(Intent.ACTION_DIAL, Uri.parse(url));
                activity.startActivity(intent);
                return true;
            } else if (url.startsWith("sms:") || url.startsWith("mailto:") || url.startsWith("whatsapp:")) {
                try {
                    Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(url));
                    activity.startActivity(intent);
                } catch (Exception ignored) {}
                return true;
            } else if (url.contains("/download/apk") || url.endsWith(".apk")) {
                try {
                    Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(url));
                    activity.startActivity(intent);
                } catch (Exception ignored) {}
                return true;
            }
            return false;
        }

        @Override
        public void onReceivedError(WebView view, int errorCode, String description, String failingUrl) {
            view.loadUrl(DEFAULT_URL);
        }
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            getWindow().setStatusBarColor(android.graphics.Color.parseColor("#7A1F2B"));
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                getWindow().setNavigationBarColor(android.graphics.Color.parseColor("#ffffff"));
                getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR);
            }
        }
        setContentView(R.layout.activity_main);

        webView = findViewById(R.id.webView);
        progressBar = findViewById(R.id.progressBar);
        btnSettings = findViewById(R.id.btnSettings);

        if (btnSettings != null) {
            btnSettings.setOnClickListener(new SettingsClickListener(this));
        }

        sirenPlayer = new SirenPlayer();
        initWebView();
        initShakeDetection();
        checkAndRequestPermissions();

        loadCurrentServer();

        // Check if user has explicitly configured a server URL; if not, probe LAN server in background
        SharedPreferences prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        if (!prefs.contains(PREF_SERVER_URL)) {
            new LanProbeThread(this).start();
        }
    }

    public void showToast(String message) {
        runOnUiThread(new ToastRunner(this, message));
    }

    public String getServerUrl() {
        SharedPreferences prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        String url = prefs.getString(PREF_SERVER_URL, DEFAULT_URL);
        if (url == null || url.contains("10.0.2.2") || url.trim().isEmpty()) {
            return DEFAULT_URL;
        }
        return url;
    }

    public void setServerUrl(String url) {
        if (!url.endsWith("/")) {
            url = url + "/";
        }
        SharedPreferences prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        prefs.edit().putString(PREF_SERVER_URL, url).apply();
        if (webView != null) {
            webView.loadUrl(url);
        }
    }

    public void loadCurrentServer() {
        String url = getServerUrl();
        if (webView != null) {
            webView.loadUrl(url);
        }
    }

    public void showServerConfigDialog() {
        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle("Server Connection Settings");
        builder.setMessage("Enter the URL of your Women Safety Shield platform:");

        final EditText input = new EditText(this);
        input.setSingleLine(true);
        input.setText(getServerUrl());
        input.setSelection(input.getText().length());
        builder.setView(input);

        builder.setPositiveButton("Connect", new DialogConnectListener(this, input));
        builder.setNeutralButton("Reset Default", new DialogResetListener(this));
        builder.setNegativeButton("Cancel", null);
        builder.show();
    }

    private static class DialogConnectListener implements DialogInterface.OnClickListener {
        private final MainActivity activity;
        private final EditText input;

        public DialogConnectListener(MainActivity activity, EditText input) {
            this.activity = activity;
            this.input = input;
        }

        @Override
        public void onClick(DialogInterface dialog, int which) {
            String newUrl = input.getText().toString().trim();
            if (!newUrl.startsWith("http://") && !newUrl.startsWith("https://")) {
                newUrl = "http://" + newUrl;
            }
            activity.setServerUrl(newUrl);
            Toast.makeText(activity, "Connecting to: " + newUrl, Toast.LENGTH_SHORT).show();
        }
    }

    private static class DialogResetListener implements DialogInterface.OnClickListener {
        private final MainActivity activity;

        public DialogResetListener(MainActivity activity) {
            this.activity = activity;
        }

        @Override
        public void onClick(DialogInterface dialog, int which) {
            activity.setServerUrl(DEFAULT_URL);
            Toast.makeText(activity, "Reset to: " + DEFAULT_URL, Toast.LENGTH_SHORT).show();
        }
    }

    private void initWebView() {
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setGeolocationEnabled(true);
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(true);
        settings.setAllowFileAccessFromFileURLs(true);
        settings.setAllowUniversalAccessFromFileURLs(true);
        settings.setMediaPlaybackRequiresUserGesture(false);
        settings.setUseWideViewPort(true);
        settings.setLoadWithOverviewMode(true);
        settings.setSupportZoom(false);
        settings.setBuiltInZoomControls(false);
        settings.setDisplayZoomControls(false);
        webView.setOverScrollMode(View.OVER_SCROLL_NEVER);
        webView.setVerticalScrollBarEnabled(false);
        webView.setHorizontalScrollBarEnabled(false);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            settings.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
        }
        settings.setUserAgentString(settings.getUserAgentString() + " WomenSafetyShieldAPK/3.2.0");

        webView.addJavascriptInterface(new AndroidBridge(this, sirenPlayer), "AndroidBridge");
        webView.setWebChromeClient(new ChromeClientImpl(this));
        webView.setWebViewClient(new WebClientImpl(this));
    }

    private void initShakeDetection() {
        sensorManager = (SensorManager) getSystemService(Context.SENSOR_SERVICE);
        if (sensorManager != null) {
            accelerometer = sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER);
            shakeDetector = new HardwareShakeDetector();
            shakeDetector.setOnShakeListener(new ShakeListenerImpl(this));
        }
    }

    public void handlePanicShake() {
        Toast.makeText(this, "🚨 PANIC SHAKE DETECTED! Triggering Distress Broadcast...", Toast.LENGTH_LONG).show();
        if (webView != null) {
            String script = "if (typeof openSosModal === 'function') { openSosModal('shake'); } " +
                    "else if (typeof enterSamePageEmergencyMode === 'function') { enterSamePageEmergencyMode(); } " +
                    "if (typeof window.onNativeShakeDetected === 'function') { window.onNativeShakeDetected(); }";
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.KITKAT) {
                webView.evaluateJavascript(script, null);
            } else {
                webView.loadUrl("javascript:" + script);
            }
        }
    }

    private void checkAndRequestPermissions() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            String[] permissions = {
                    Manifest.permission.ACCESS_FINE_LOCATION,
                    Manifest.permission.ACCESS_COARSE_LOCATION,
                    Manifest.permission.CAMERA,
                    Manifest.permission.RECORD_AUDIO,
                    Manifest.permission.CALL_PHONE
            };
            boolean needsRequest = false;
            for (String perm : permissions) {
                if (checkSelfPermission(perm) != PackageManager.PERMISSION_GRANTED) {
                    needsRequest = true;
                    break;
                }
            }
            if (needsRequest) {
                requestPermissions(permissions, PERMISSION_REQUEST_CODE);
            }
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (sensorManager != null && accelerometer != null && shakeDetector != null) {
            sensorManager.registerListener(shakeDetector, accelerometer, SensorManager.SENSOR_DELAY_UI);
        }
    }

    @Override
    protected void onPause() {
        if (sensorManager != null && shakeDetector != null) {
            sensorManager.unregisterListener(shakeDetector);
        }
        super.onPause();
    }

    @Override
    protected void onDestroy() {
        if (sirenPlayer != null) {
            sirenPlayer.stop();
        }
        if (webView != null) {
            webView.destroy();
        }
        super.onDestroy();
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        if (requestCode == FILE_CHOOSER_REQUEST_CODE) {
            if (uploadMessage != null) {
                Uri[] results = null;
                if (resultCode == Activity.RESULT_OK && data != null) {
                    String dataString = data.getDataString();
                    if (dataString != null) {
                        results = new Uri[]{Uri.parse(dataString)};
                    }
                }
                uploadMessage.onReceiveValue(results);
                uploadMessage = null;
            }
        }
        super.onActivityResult(requestCode, resultCode, data);
    }

    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
            return;
        }

        if (backPressedTime + 2000 > System.currentTimeMillis()) {
            super.onBackPressed();
        } else {
            Toast.makeText(this, "Press back again to exit Women Safety Shield", Toast.LENGTH_SHORT).show();
            backPressedTime = System.currentTimeMillis();
        }
    }
}
