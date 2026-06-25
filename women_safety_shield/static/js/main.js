// Women Safety Shield - Main JS

// Get user location
function getUserLocation(callback) {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            pos => callback(pos.coords.latitude, pos.coords.longitude, null),
            err => callback(null, null, err.message),
            { enableHighAccuracy: true, timeout: 10000 }
        );
    } else {
        callback(null, null, 'Geolocation not supported');
    }
}

// Shake detection for SOS
let lastX = null, lastY = null, lastZ = null;
const SHAKE_THRESHOLD = 20;
let shakeCount = 0;
let lastShakeTime = 0;

if (window.DeviceMotionEvent) {
    window.addEventListener('devicemotion', function(e) {
        const acc = e.accelerationIncludingGravity;
        if (!acc) return;
        const {x, y, z} = acc;

        if (lastX !== null) {
            const delta = Math.abs(x - lastX) + Math.abs(y - lastY) + Math.abs(z - lastZ);
            const now = Date.now();

            if (delta > SHAKE_THRESHOLD) {
                if (now - lastShakeTime < 500) {
                    shakeCount++;
                    if (shakeCount >= 3) {
                        shakeCount = 0;
                        document.dispatchEvent(new CustomEvent('shakeDetected'));
                    }
                } else {
                    shakeCount = 1;
                }
                lastShakeTime = now;
            }
        }
        lastX = x; lastY = y; lastZ = z;
    });
}

// CSRF token helper
function getCsrfToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
           document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '';
}

// SOS trigger via JS
async function triggerSOSWithLocation(triggerType = 'button') {
    const btn = document.getElementById('sosButton');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Getting Location...';
    }

    getUserLocation(async (lat, lng, err) => {
        if (err || !lat) {
            alert('⚠️ Could not get your location. Please allow location access and try again.\n' + (err || ''));
            if (btn) { btn.disabled = false; btn.innerHTML = '🆘<br>SOS'; }
            return;
        }

        if (btn) btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Sending Alert...';

        document.getElementById('sos_lat').value = lat;
        document.getElementById('sos_lng').value = lng;
        document.getElementById('sos_trigger').value = triggerType;
        document.getElementById('sosForm').submit();
    });
}

// Copy to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard!', 'success');
    });
}

// Toast notification
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} alert-dismissible fade show shadow position-fixed`;
    toast.style.cssText = 'bottom:20px;right:20px;z-index:9999;min-width:250px;';
    toast.innerHTML = `${message}<button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
}

// WebSocket location tracking
class LocationTracker {
    constructor(emergencyId) {
        this.emergencyId = emergencyId;
        this.ws = null;
        this.watchId = null;
    }

    start() {
        const wsScheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
        this.ws = new WebSocket(`${wsScheme}://${window.location.host}/ws/emergency/${this.emergencyId}/`);

        this.ws.onopen = () => {
            console.log('Emergency WS connected');
            this.startTracking();
        };

        this.ws.onclose = () => {
            console.log('WS disconnected');
            setTimeout(() => this.reconnect(), 3000);
        };

        this.ws.onerror = (e) => console.error('WS error', e);
    }

    startTracking() {
        if (navigator.geolocation) {
            this.watchId = navigator.geolocation.watchPosition(
                pos => this.sendLocation(pos.coords.latitude, pos.coords.longitude),
                err => console.error('Location error:', err),
                { enableHighAccuracy: true, maximumAge: 5000, timeout: 10000 }
            );
        }
    }

    sendLocation(lat, lng) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'location',
                latitude: lat,
                longitude: lng,
                emergency_id: this.emergencyId,
                timestamp: new Date().toISOString()
            }));
        }
    }

    stop() {
        if (this.watchId) navigator.geolocation.clearWatch(this.watchId);
        if (this.ws) this.ws.close();
    }

    reconnect() {
        this.start();
    }
}

// Format distance
function formatDistance(km) {
    if (km < 1) return `${Math.round(km * 1000)}m`;
    return `${km.toFixed(1)}km`;
}

// Format time ago
function timeAgo(dateStr) {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = Math.floor((now - date) / 1000);
    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff/60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff/3600)}h ago`;
    return `${Math.floor(diff/86400)}d ago`;
}

// Trust score stars
function trustStars(score) {
    const full = Math.floor(score / 2);
    const half = (score % 2) >= 1 ? 1 : 0;
    let html = '';
    for (let i = 0; i < full; i++) html += '★';
    if (half) html += '½';
    return html;
}
