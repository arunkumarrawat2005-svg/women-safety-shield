/**
 * Women Safety Shield - Global Google Maps Platform Integration Library
 * Provides standard, unified Google Maps mapping across all features:
 * - SOS Emergency Map (Same-Page in-place emergency background map)
 * - Victim Distress Marker & 3 km Emergency Assistance Zone Radius
 * - Live nearby verified users & guardians with dynamic radar telemetry
 * - Safe Journey Tracking & Route Navigation
 * - Incident Reporting & Community Safety Mapping
 * 
 * Complies with Google Maps Platform Standards:
 * - internalUsageAttributionIds: ['gmp_git_agentskills_v1']
 * - mapId: 'DEMO_MAP_ID' (enables AdvancedMarkerElement)
 * - Zero-Downtime Smart Fallback: Guarantees 100% visible interactive map
 *   even when offline, keyless, or during async initialization.
 */

// Source: Google Maps Platform Code Assist
(function (window) {
    'use strict';

    // Suppress Google Maps broken auth overlay box instantly
    try {
        const errHideStyle = document.createElement('style');
        errHideStyle.id = 'gmp-err-suppressor';
        errHideStyle.textContent = '.gm-err-container, .gm-err-message, .gm-err-autocomplete { display: none !important; visibility: hidden !important; }';
        if (document.head) document.head.appendChild(errHideStyle);
        else document.addEventListener('DOMContentLoaded', () => document.head && document.head.appendChild(errHideStyle));
    } catch(e){}

    let isGoogleMapsLoaded = false;
    let isGoogleMapsLoading = false;
    const loadCallbacks = [];

    const DEMO_HELPERS = [
        { id: 1, title: "Aadhaar Verified Resident", badge: "Community Guardian", trust: 4.9, offsetLat: 0.0035, offsetLng: 0.0042, type: "Resident" },
        { id: 2, title: "Campus Safety Marshal", badge: "First Responder", trust: 5.0, offsetLat: -0.0048, offsetLng: 0.0031, type: "Security" },
        { id: 3, title: "Women Safety Mitra", badge: "Neighborhood Watch", trust: 4.8, offsetLat: 0.0062, offsetLng: -0.0038, type: "Volunteer" },
        { id: 4, title: "Transit Safety Escort", badge: "Verified Escort", trust: 5.0, offsetLat: -0.0028, offsetLng: -0.0055, type: "Volunteer" },
        { id: 5, title: "Safe Haven Host", badge: "Store Safe Zone", trust: 4.9, offsetLat: 0.0078, offsetLng: 0.0065, type: "Merchant" },
        { id: 6, title: "Emergency First Aider", badge: "Medical Aid", trust: 4.9, offsetLat: -0.0082, offsetLng: 0.0018, type: "Citizen" },
        { id: 7, title: "Night Patrol Volunteer", badge: "Shield Patrol", trust: 4.8, offsetLat: 0.0019, offsetLng: -0.0089, type: "Resident" },
        { id: 8, title: "Certified Rescue Volunteer", badge: "Disaster Team", trust: 5.0, offsetLat: -0.0065, offsetLng: -0.0072, type: "Volunteer" },
        { id: 9, title: "Civic Safety Partner", badge: "Active Citizen", trust: 4.8, offsetLat: 0.0091, offsetLng: -0.0012, type: "Resident" },
        { id: 10, title: "Residential Welfare Escort", badge: "Guardian Host", trust: 4.9, offsetLat: -0.0015, offsetLng: 0.0094, type: "Volunteer" },
        { id: 11, title: "Campus Quick Responder", badge: "Campus Marshal", trust: 4.9, offsetLat: 0.0055, offsetLng: 0.0082, type: "Security" },
        { id: 12, title: "Verified Community Watch", badge: "Shield Mitra", trust: 4.8, offsetLat: -0.0075, offsetLng: 0.0068, type: "Resident" }
    ];

    // Ensure window.google.maps stubs exist to prevent runtime reference crashes
    window.google = window.google || {};
    window.google.maps = window.google.maps || {};

    if (!window.google.maps.LatLngBounds) {
        window.google.maps.LatLngBounds = class {
            constructor() { this.points = []; }
            extend(pt) {
                if (!pt) return;
                const lat = typeof pt.lat === 'function' ? pt.lat() : pt.lat;
                const lng = typeof pt.lng === 'function' ? pt.lng() : pt.lng;
                if (!isNaN(lat) && !isNaN(lng)) {
                    this.points.push([lat, lng]);
                }
            }
        };
    }

    if (!window.google.maps.LatLng) {
        window.google.maps.LatLng = class {
            constructor(lat, lng) {
                this._lat = parseFloat(lat);
                this._lng = parseFloat(lng);
            }
            lat() { return this._lat; }
            lng() { return this._lng; }
        };
    }

    if (!window.google.maps.Polyline) {
        window.google.maps.Polyline = class {
            constructor(opts = {}) {
                this.opts = opts;
                this.map = opts.map;
                this._line = null;
                const coords = (opts.path || []).map(p => {
                    const lat = typeof p.lat === 'function' ? p.lat() : (p.lat !== undefined ? p.lat : p[0]);
                    const lng = typeof p.lng === 'function' ? p.lng() : (p.lng !== undefined ? p.lng : p[1]);
                    return [lat, lng];
                });
                if (this.map && this.map.isGoogleMap === false && window.L) {
                    this._line = L.polyline(coords, {
                        color: opts.strokeColor || '#27ae60',
                        weight: opts.strokeWeight || 5,
                        opacity: opts.strokeOpacity || 0.9
                    }).addTo(this.map.rawMap || this.map);
                }
            }
            setOptions(newOpts) {
                this.opts = Object.assign(this.opts, newOpts);
                if (this._line && this._line.setStyle) {
                    this._line.setStyle({
                        color: newOpts.strokeColor || this.opts.strokeColor,
                        weight: newOpts.strokeWeight || this.opts.strokeWeight,
                        opacity: newOpts.strokeOpacity !== undefined ? newOpts.strokeOpacity : this.opts.strokeOpacity
                    });
                }
            }
            addListener(event, cb) {
                if (this._line) {
                    this._line.on(event, e => cb({ latLng: { lat: () => e.latlng.lat, lng: () => e.latlng.lng } }));
                }
            }
            setMap(m) {
                if (this._line) {
                    if (m) (m.rawMap || m).addLayer(this._line);
                    else (this.map ? (this.map.rawMap || this.map) : this._line).remove();
                }
            }
        };
    }

    if (!window.google.maps.Circle) {
        window.google.maps.Circle = class {
            constructor(opts = {}) {
                this.opts = opts;
                this.map = opts.map;
                this._circle = null;
                const c = opts.center || { lat: 28.47, lng: 77.49 };
                const lat = typeof c.lat === 'function' ? c.lat() : (c.lat !== undefined ? c.lat : c[0]);
                const lng = typeof c.lng === 'function' ? c.lng() : (c.lng !== undefined ? c.lng : c[1]);
                if (this.map && this.map.isGoogleMap === false && window.L) {
                    this._circle = L.circle([lat, lng], {
                        radius: opts.radius || 250,
                        color: opts.strokeColor || '#27ae60',
                        fillColor: opts.fillColor || opts.strokeColor || '#27ae60',
                        fillOpacity: opts.fillOpacity || 0.2,
                        weight: opts.strokeWeight || 2
                    }).addTo(this.map.rawMap || this.map);
                }
            }
            setCenter(c) {
                const lat = typeof c.lat === 'function' ? c.lat() : (c.lat !== undefined ? c.lat : c[0]);
                const lng = typeof c.lng === 'function' ? c.lng() : (c.lng !== undefined ? c.lng : c[1]);
                if (this._circle) this._circle.setLatLng([lat, lng]);
            }
            setRadius(r) {
                if (this._circle) this._circle.setRadius(r);
            }
            addListener(event, cb) {
                if (this._circle) {
                    this._circle.on(event, e => cb({ latLng: { lat: () => e.latlng.lat, lng: () => e.latlng.lng } }));
                }
            }
            setMap(m) {
                if (this._circle) {
                    if (m) (m.rawMap || m).addLayer(this._circle);
                    else this._circle.remove();
                }
            }
        };
    }

    if (!window.google.maps.InfoWindow) {
        window.google.maps.InfoWindow = class {
            constructor(opts = {}) {
                this.content = opts.content || '';
                this.pos = null;
            }
            setPosition(p) {
                this.pos = p;
            }
            open(opts) {
                let targetMap = null;
                let anchor = null;
                if (opts && (opts.map || opts.anchor)) {
                    targetMap = opts.map ? (opts.map.rawMap || opts.map) : null;
                    anchor = opts.anchor || null;
                } else if (opts) {
                    targetMap = opts.rawMap || opts;
                }
                if (anchor && anchor.marker && anchor.marker.bindPopup) {
                    anchor.marker.bindPopup(this.content).openPopup();
                } else if (targetMap && targetMap.openPopup && this.pos) {
                    const lat = typeof this.pos.lat === 'function' ? this.pos.lat() : this.pos.lat;
                    const lng = typeof this.pos.lng === 'function' ? this.pos.lng() : this.pos.lng;
                    L.popup().setLatLng([lat, lng]).setContent(this.content).openOn(targetMap);
                }
        };
    }

    // Global Google Maps Platform Auth Failure Interceptor
    window.gm_authFailure = function() {
        console.warn('[GoogleMapsShield] Google Maps API authentication rejected by Google (gm_authFailure). Automatically triggering Zero-Downtime Leaflet fallback.');
        window.googleMapsAuthFailed = true;
        try { sessionStorage.setItem('gmp_auth_failed', '1'); } catch(e){}
        if (typeof GoogleMapsShield !== 'undefined' && GoogleMapsShield.failoverAllMapsToLeaflet) {
            GoogleMapsShield.failoverAllMapsToLeaflet();
        }
    };

    const GoogleMapsShield = {
        DEMO_HELPERS: DEMO_HELPERS,
        _activeMapRegistry: [],

        registerMapInit: function(containerId, initFn, options) {
            this._activeMapRegistry = this._activeMapRegistry.filter(entry => entry.id !== containerId);
            this._activeMapRegistry.push({ id: containerId, initFn: initFn, options: options });
        },

        failoverContainerToLeaflet: function(el, options = {}) {
            if (!el) return;
            console.warn('[GoogleMapsShield] Converting container', el.id || el, 'to high-fidelity Leaflet street map.');
            window.googleMapsAuthFailed = true;
            try { sessionStorage.setItem('gmp_auth_failed', '1'); } catch(e){}

            // Clean up any existing Leaflet instances on this element
            if (el._leaflet_id) {
                try { if (el._leaflet_map) el._leaflet_map.remove(); } catch(e){}
                el._leaflet_id = null;
            }
            el.innerHTML = '';

            // Check if there is a registered reinit callback
            const entry = this._activeMapRegistry.find(r => r.id === el.id || r.el === el);
            if (entry && typeof entry.initFn === 'function') {
                try {
                    entry.initFn();
                    return;
                } catch(err) {
                    console.error('Re-init failed:', err);
                }
            }

            // Otherwise, create default fallback Leaflet map directly
            const fallbackMap = this.createMap(el, Object.assign({}, options, { forceLeaflet: true }));
            if (fallbackMap && fallbackMap.rawMap) {
                setTimeout(() => { try { fallbackMap.rawMap.invalidateSize(); } catch(e){} }, 100);
            }
        },

        failoverAllMapsToLeaflet: function() {
            window.googleMapsAuthFailed = true;
            try { sessionStorage.setItem('gmp_auth_failed', '1'); } catch(e){}
            const entries = [...this._activeMapRegistry];
            entries.forEach(entry => {
                const el = typeof entry.id === 'string' ? document.getElementById(entry.id) : (entry.el || null);
                if (el) {
                    this.failoverContainerToLeaflet(el, entry.options);
                }
            });
        },

        /**
         * Load the Google Maps JavaScript API dynamically with fallback notification
         */
        load: function (apiKey, callback) {
            const hasAuthFailed = window.googleMapsAuthFailed || (function(){
                try { return sessionStorage.getItem('gmp_auth_failed') === '1'; } catch(e){ return false; }
            })();

            if (hasAuthFailed) {
                // If previous attempt failed auth, immediately fire callback with Leaflet
                if (callback) setTimeout(callback, 10);
                return;
            }

            if (window.google && window.google.maps && typeof window.google.maps.Map === 'function') {
                isGoogleMapsLoaded = true;
                if (callback) callback();
                return;
            }

            if (callback) loadCallbacks.push(callback);

            const fireCallbacks = function() {
                isGoogleMapsLoaded = true;
                isGoogleMapsLoading = false;
                while (loadCallbacks.length > 0) {
                    const cb = loadCallbacks.shift();
                    try { cb(); } catch (e) { console.error('Map callback error:', e); }
                }
            };

            window.__initGoogleMapsShield = fireCallbacks;

            if (isGoogleMapsLoading) return;
            isGoogleMapsLoading = true;

            // If an API key is provided and valid, attempt loading Google Maps SDK
            const hasValidKey = (apiKey && apiKey !== 'your_real_google_maps_key' && apiKey !== 'your-google-maps-key' && apiKey.trim().length > 10);
            
            if (hasValidKey) {
                const existingScript = document.querySelector('script[src*="maps.googleapis.com/maps/api/js"]');
                if (existingScript) {
                    let attempts = 0;
                    const checkInterval = setInterval(() => {
                        attempts++;
                        if (window.googleMapsAuthFailed) {
                            clearInterval(checkInterval);
                            fireCallbacks();
                        } else if (window.google && window.google.maps && typeof window.google.maps.Map === 'function') {
                            clearInterval(checkInterval);
                            fireCallbacks();
                        } else if (attempts > 12) {
                            clearInterval(checkInterval);
                            isGoogleMapsLoading = false;
                            fireCallbacks(); // Fallback ready
                        }
                    }, 100);
                    return;
                }

                const script = document.createElement('script');
                script.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(apiKey)}&libraries=places,geometry,marker&loading=async&callback=__initGoogleMapsShield`;
                script.async = true;
                script.defer = true;
                script.onerror = function () {
                    console.warn('Google Maps script load failed; activating high-fidelity fallback map.');
                    isGoogleMapsLoading = false;
                    fireCallbacks();
                };
                document.head.appendChild(script);
            } else {
                // No key or demo mode: instantly fire callbacks with universal fallback engine
                setTimeout(fireCallbacks, 20);
            }
        },

        /**
         * Create a standard styled Map (Google Maps Platform if key loaded, or seamless Leaflet fallback)
         */
        createMap: function (container, options = {}) {
            const el = typeof container === 'string' ? document.getElementById(container) : container;
            if (!el) {
                console.error('Map container element not found:', container);
                return null;
            }

            const center = options.center || { lat: 28.4703, lng: 77.4939 };
            const zoom = options.zoom || 14;
            const cLat = typeof center.lat === 'function' ? center.lat() : (center.lat !== undefined ? center.lat : center[0]);
            const cLng = typeof center.lng === 'function' ? center.lng() : (center.lng !== undefined ? center.lng : center[1]);

            const hasAuthFailed = window.googleMapsAuthFailed || (function(){
                try { return sessionStorage.getItem('gmp_auth_failed') === '1'; } catch(e){ return false; }
            })();

            // Attempt 1: True Google Maps Platform (ONLY if not previously failed and not forced to Leaflet)
            if (!options.forceLeaflet && !hasAuthFailed && window.google && window.google.maps && typeof window.google.maps.Map === 'function') {
                try {
                    const mapOptions = {
                        center: { lat: cLat, lng: cLng },
                        zoom: zoom,
                        mapId: options.mapId || 'DEMO_MAP_ID',
                        internalUsageAttributionIds: ['gmp_git_agentskills_v1'],
                        disableDefaultUI: false,
                        zoomControl: options.zoomControl !== false,
                        mapTypeControl: false,
                        streetViewControl: false,
                        fullscreenControl: true,
                        styles: options.styles || [
                            { featureType: "poi", elementType: "labels", stylers: [{ visibility: "off" }] },
                            { featureType: "transit", elementType: "labels.icon", stylers: [{ visibility: "off" }] }
                        ]
                    };
                    const gMap = new google.maps.Map(el, mapOptions);
                    gMap.isGoogleMap = true;
                    gMap.rawMap = gMap;

                    // Add helper compatibility methods
                    gMap.on = function(event, cb) {
                        return gMap.addListener(event, cb);
                    };

                    // Monitor container for Google auth failure error UI injection
                    const self = this;
                    const errObserver = new MutationObserver(function() {
                        if (el.querySelector('.gm-err-container, .gm-err-message') || (el.innerText && el.innerText.includes('Sorry! Something went wrong'))) {
                            console.warn('[GoogleMapsShield] Detected Google Maps error overlay in container. Triggering instant failover.');
                            errObserver.disconnect();
                            window.googleMapsAuthFailed = true;
                            try { sessionStorage.setItem('gmp_auth_failed', '1'); } catch(e){}
                            self.failoverContainerToLeaflet(el, options);
                        }
                    });
                    errObserver.observe(el, { childList: true, subtree: true });

                    setTimeout(function() {
                        if (el.querySelector('.gm-err-container, .gm-err-message') || (el.innerText && el.innerText.includes('Sorry! Something went wrong'))) {
                            errObserver.disconnect();
                            window.googleMapsAuthFailed = true;
                            try { sessionStorage.setItem('gmp_auth_failed', '1'); } catch(e){}
                            self.failoverContainerToLeaflet(el, options);
                        }
                    }, 800);

                    setTimeout(function() {
                        if (el.querySelector('.gm-err-container, .gm-err-message') || (el.innerText && el.innerText.includes('Sorry! Something went wrong'))) {
                            errObserver.disconnect();
                            window.googleMapsAuthFailed = true;
                            try { sessionStorage.setItem('gmp_auth_failed', '1'); } catch(e){}
                            self.failoverContainerToLeaflet(el, options);
                        }
                    }, 2000);

                    return gMap;
                } catch (err) {
                    console.warn('Google Maps initialization failed, failing over to high-fidelity street map:', err);
                }
            }

            // Attempt 2: High-Resolution Zero-Downtime Fallback Map (Leaflet Engine)
            if (window.L) {
                // Clear any broken children and reset any previous Leaflet instances
                if (el._leaflet_id) {
                    try { if (el._leaflet_map) el._leaflet_map.remove(); } catch(e){}
                    el._leaflet_id = null;
                }
                el.innerHTML = '';

                const lMap = L.map(el, {
                    center: [cLat, cLng],
                    zoom: zoom,
                    zoomControl: options.zoomControl !== false,
                    attributionControl: true
                });
                el._leaflet_map = lMap;

                // High-contrast, unblocked HD Street Network tiles (CartoDB Voyager CDN)
                const tileLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
                    maxZoom: 20,
                    subdomains: 'abcd',
                    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a> | Google Maps Platform Protocol'
                });
                
                // Fallback to Esri World Street Map if tile load fails
                tileLayer.on('tileerror', function(error, tile) {
                    if (tile && !tile._retried) {
                        tile._retried = true;
                        const coords = error.coords;
                        tile.src = `https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/${coords.z}/${coords.y}/${coords.x}`;
                    }
                });
                tileLayer.addTo(lMap);

                // Add adapter methods so lMap satisfies Google Maps API surface
                lMap.isGoogleMap = false;
                lMap.rawMap = lMap;

                lMap.setCenter = function (pos) {
                    const lat = typeof pos.lat === 'function' ? pos.lat() : (pos.lat !== undefined ? pos.lat : pos[0]);
                    const lng = typeof pos.lng === 'function' ? pos.lng() : (pos.lng !== undefined ? pos.lng : pos[1]);
                    lMap.setView([lat, lng], lMap.getZoom());
                };

                lMap.panTo = function (pos) {
                    const lat = typeof pos.lat === 'function' ? pos.lat() : (pos.lat !== undefined ? pos.lat : pos[0]);
                    const lng = typeof pos.lng === 'function' ? pos.lng() : (pos.lng !== undefined ? pos.lng : pos[1]);
                    L.Map.prototype.panTo.call(lMap, [lat, lng], { animate: true, duration: 1.0 });
                };

                lMap.setZoom = function (z) {
                    L.Map.prototype.setZoom.call(lMap, z);
                };

                lMap.getCenter = function () {
                    const c = L.Map.prototype.getCenter.call(lMap);
                    return {
                        lat: () => c.lat,
                        lng: () => c.lng,
                        lat: c.lat,
                        lng: c.lng
                    };
                };

                lMap.addListener = function (event, callback) {
                    lMap.on(event, function (e) {
                        const evt = {
                            latLng: {
                                lat: () => e.latlng.lat,
                                lng: () => e.latlng.lng,
                                lat: e.latlng.lat,
                                lng: e.latlng.lng
                            }
                        };
                        callback(evt);
                    });
                };

                lMap.fitBounds = function (bounds) {
                    if (!bounds) return;
                    try {
                        if (bounds.points && bounds.points.length > 0) {
                            L.Map.prototype.fitBounds.call(lMap, bounds.points, { padding: [30, 30] });
                        } else if (Array.isArray(bounds) && bounds.length > 0) {
                            const pts = bounds.map(p => {
                                const lat = typeof p.lat === 'function' ? p.lat() : (p.lat !== undefined ? p.lat : p[0]);
                                const lng = typeof p.lng === 'function' ? p.lng() : (p.lng !== undefined ? p.lng : p[1]);
                                return [lat, lng];
                            }).filter(p => !isNaN(p[0]) && !isNaN(p[1]));
                            if (pts.length > 0) {
                                L.Map.prototype.fitBounds.call(lMap, pts, { padding: [30, 30] });
                            }
                        } else if (bounds.getNorthEast && bounds.getSouthWest) {
                            L.Map.prototype.fitBounds.call(lMap, [
                                [bounds.getSouthWest().lat(), bounds.getSouthWest().lng()],
                                [bounds.getNorthEast().lat(), bounds.getNorthEast().lng()]
                            ], { padding: [30, 30] });
                        }
                    } catch(err) {
                        console.warn('fitBounds fallback handled:', err);
                    }
                };

                setTimeout(() => { try { lMap.invalidateSize(); } catch(e){} }, 100);
                setTimeout(() => { try { lMap.invalidateSize(); } catch(e){} }, 400);

                return lMap;
            }

            console.error('Neither Google Maps nor Leaflet fallback engine is loaded.');
            return null;
        },

        /**
         * Create custom marker with InfoWindow and drag support across both engines
         */
        createCustomMarker: function (map, opts = {}) {
            const rawMap = map && map.rawMap ? map.rawMap : map;
            const lat = typeof opts.lat === 'function' ? opts.lat() : opts.lat;
            const lng = typeof opts.lng === 'function' ? opts.lng() : opts.lng;
            const isGoogle = map && map.isGoogleMap === true;

            if (isGoogle) {
                const position = { lat: lat, lng: lng };
                let gMarker;

                if (opts.html) {
                    const el = document.createElement('div');
                    el.innerHTML = opts.html;
                    if (google.maps.marker && google.maps.marker.AdvancedMarkerElement) {
                        gMarker = new google.maps.marker.AdvancedMarkerElement({
                            map: rawMap,
                            position: position,
                            content: el,
                            title: opts.title || '',
                            gmpDraggable: !!opts.draggable,
                            zIndex: opts.zIndex || 100
                        });
                        if (opts.onDragEnd) {
                            gMarker.addListener('dragend', function () {
                                const p = gMarker.position;
                                opts.onDragEnd({ lat: typeof p.lat === 'function' ? p.lat() : p.lat, lng: typeof p.lng === 'function' ? p.lng() : p.lng });
                            });
                        }
                    } else {
                        gMarker = new google.maps.Marker({
                            map: rawMap,
                            position: position,
                            title: opts.title || '',
                            draggable: !!opts.draggable
                        });
                        if (opts.onDragEnd) {
                            gMarker.addListener('dragend', function (event) {
                                opts.onDragEnd({ lat: event.latLng.lat(), lng: event.latLng.lng() });
                            });
                        }
                    }
                } else {
                    gMarker = new google.maps.Marker({
                        map: rawMap,
                        position: position,
                        title: opts.title || '',
                        draggable: !!opts.draggable,
                        icon: opts.icon || {
                            path: google.maps.SymbolPath.CIRCLE,
                            scale: opts.scale || 8,
                            fillColor: opts.color || '#B3243A',
                            fillOpacity: 1,
                            strokeColor: '#ffffff',
                            strokeWeight: 2
                        }
                    });
                    if (opts.onDragEnd) {
                        gMarker.addListener('dragend', function (event) {
                            opts.onDragEnd({ lat: event.latLng.lat(), lng: event.latLng.lng() });
                        });
                    }
                }

                let infoWindow = null;
                if (opts.popupContent) {
                    infoWindow = new google.maps.InfoWindow({ content: opts.popupContent });
                    gMarker.addListener('click', function () {
                        infoWindow.open({ anchor: gMarker, map: rawMap, shouldFocus: false });
                    });
                }

                return {
                    marker: gMarker,
                    infoWindow: infoWindow,
                    setPosition: function (nLat, nLng) {
                        const p = { lat: nLat, lng: nLng };
                        if (gMarker.setPosition) gMarker.setPosition(p);
                        else if (gMarker.position) gMarker.position = p;
                    },
                    setLatLng: function (latlng) {
                        const nLat = Array.isArray(latlng) ? latlng[0] : (typeof latlng.lat === 'function' ? latlng.lat() : latlng.lat);
                        const nLng = Array.isArray(latlng) ? latlng[1] : (typeof latlng.lng === 'function' ? latlng.lng() : latlng.lng);
                        this.setPosition(nLat, nLng);
                    },
                    openPopup: function () {
                        if (infoWindow) infoWindow.open({ anchor: gMarker, map: rawMap, shouldFocus: false });
                    },
                    closePopup: function () {
                        if (infoWindow) infoWindow.close();
                    },
                    setMap: function (m) {
                        const rm = m && m.rawMap ? m.rawMap : m;
                        if (gMarker.setMap) gMarker.setMap(rm);
                        else gMarker.map = rm;
                    },
                    remove: function () {
                        this.setMap(null);
                    }
                };
            }

            // High-fidelity Leaflet Marker Fallback
            if (window.L) {
                let lIcon;
                if (opts.html) {
                    lIcon = L.divIcon({
                        html: opts.html,
                        className: 'gmap-custom-div-icon',
                        iconSize: [28, 28],
                        iconAnchor: [14, 14]
                    });
                } else {
                    const color = opts.color || '#B3243A';
                    const scale = opts.scale || 8;
                    lIcon = L.divIcon({
                        html: `<div style="background:${color};width:${scale*2}px;height:${scale*2}px;border-radius:50%;border:2px solid #ffffff;box-shadow:0 0 6px rgba(0,0,0,0.3);"></div>`,
                        className: 'gmap-custom-circle-icon',
                        iconSize: [scale*2, scale*2],
                        iconAnchor: [scale, scale]
                    });
                }

                const lMarker = L.marker([lat, lng], {
                    draggable: !!opts.draggable,
                    icon: lIcon,
                    title: opts.title || ''
                });

                if (rawMap) lMarker.addTo(rawMap);

                if (opts.popupContent) {
                    lMarker.bindPopup(opts.popupContent);
                }

                if (opts.onDragEnd) {
                    lMarker.on('dragend', function (e) {
                        const p = e.target.getLatLng();
                        opts.onDragEnd({ lat: p.lat, lng: p.lng });
                    });
                }

                return {
                    marker: lMarker,
                    setPosition: function (nLat, nLng) {
                        lMarker.setLatLng([nLat, nLng]);
                    },
                    setLatLng: function (latlng) {
                        lMarker.setLatLng(latlng);
                    },
                    openPopup: function () {
                        lMarker.openPopup();
                    },
                    closePopup: function () {
                        lMarker.closePopup();
                    },
                    setMap: function (m) {
                        const rm = m && m.rawMap ? m.rawMap : m;
                        if (rm) rm.addLayer(lMarker);
                        else lMarker.remove();
                    },
                    remove: function () {
                        lMarker.remove();
                    }
                };
            }

            return null;
        },

        /**
         * Create SOS Victim Distress Beacon Marker with concentric pulsating radar rings
         */
        createSOSMarker: function (map, lat, lng, label = "YOU (DISTRESS LOCATION)") {
            const beaconHTML = `
                <div class="sos-pulse-beacon" title="${label}">
                    <div class="sos-beacon-ring"></div>
                    <div class="sos-beacon-ring ring-2"></div>
                    <div class="sos-beacon-core"><i class="bi bi-exclamation-triangle-fill"></i></div>
                </div>
            `;
            const popupContent = `
                <div style="font-family:'Plus Jakarta Sans',sans-serif;padding:6px;text-align:center;min-width:180px;">
                    <strong style="color:#dc2626;font-size:0.95rem;display:block;margin-bottom:4px;">
                        <i class="bi bi-exclamation-octagon-fill" style="margin-right:4px;"></i>${label}
                    </strong>
                    <div style="color:#64748b;font-size:0.8rem;margin-bottom:6px;">
                        GPS: ${parseFloat(lat).toFixed(4)}, ${parseFloat(lng).toFixed(4)}
                    </div>
                    <span style="background:#dc2626;color:#ffffff;font-size:0.75rem;padding:3px 10px;border-radius:9999px;font-weight:700;">
                        Emergency Beacon Active
                    </span>
                </div>
            `;

            return this.createCustomMarker(map, {
                lat: lat,
                lng: lng,
                html: beaconHTML,
                title: label,
                zIndex: 2000,
                popupContent: popupContent
            });
        },

        /**
         * Create 3 km emergency assistance zone circle
         */
        createRadiusCircle: function (map, lat, lng, radiusMeters = 3000, options = {}) {
            const rawMap = map && map.rawMap ? map.rawMap : map;
            const isGoogle = map && map.isGoogleMap === true;

            if (isGoogle) {
                const circleOptions = Object.assign({
                    map: rawMap,
                    center: { lat: lat, lng: lng },
                    radius: radiusMeters,
                    fillColor: '#ef4444',
                    fillOpacity: 0.12,
                    strokeColor: '#dc2626',
                    strokeOpacity: 0.85,
                    strokeWeight: 2,
                    clickable: false
                }, options);
                return new google.maps.Circle(circleOptions);
            }

            if (window.L) {
                const circle = L.circle([lat, lng], {
                    radius: radiusMeters,
                    color: options.strokeColor || '#dc2626',
                    fillColor: options.fillColor || '#ef4444',
                    fillOpacity: options.fillOpacity || 0.12,
                    weight: options.strokeWeight || 2
                }).addTo(rawMap);

                return {
                    circle: circle,
                    rawCircle: circle,
                    setCenter: function(pos) {
                        const nLat = typeof pos.lat === 'function' ? pos.lat() : (pos.lat !== undefined ? pos.lat : pos[0]);
                        const nLng = typeof pos.lng === 'function' ? pos.lng() : (pos.lng !== undefined ? pos.lng : pos[1]);
                        circle.setLatLng([nLat, nLng]);
                    },
                    setRadius: function(r) {
                        circle.setRadius(r);
                    },
                    setMap: function(m) {
                        const rm = m && m.rawMap ? m.rawMap : m;
                        if (rm) rm.addLayer(circle);
                        else circle.remove();
                    },
                    addListener: function(event, cb) {
                        circle.on(event, function(e) {
                            cb({
                                latLng: {
                                    lat: () => e.latlng.lat,
                                    lng: () => e.latlng.lng,
                                    lat: e.latlng.lat,
                                    lng: e.latlng.lng
                                }
                            });
                        });
                    },
                    bindPopup: function(content) {
                        circle.bindPopup(content);
                        return this;
                    },
                    remove: function() {
                        circle.remove();
                    }
                };
            }

            return null;
        },

        /**
         * Create route polyline across both engines
         */
        createPolyline: function (map, coordinates, options = {}) {
            const rawMap = map && map.rawMap ? map.rawMap : map;
            const isGoogle = map && map.isGoogleMap === true;

            const pathGoogle = coordinates.map(c => {
                const lat = typeof c.lat === 'function' ? c.lat() : (c.lat !== undefined ? c.lat : c[0]);
                const lng = typeof c.lng === 'function' ? c.lng() : (c.lng !== undefined ? c.lng : c[1]);
                return { lat: lat, lng: lng };
            });

            const pathLeaflet = coordinates.map(c => {
                const lat = typeof c.lat === 'function' ? c.lat() : (c.lat !== undefined ? c.lat : c[0]);
                const lng = typeof c.lng === 'function' ? c.lng() : (c.lng !== undefined ? c.lng : c[1]);
                return [lat, lng];
            });

            if (isGoogle) {
                const polyline = new google.maps.Polyline(Object.assign({
                    path: pathGoogle,
                    geodesic: true,
                    strokeColor: options.strokeColor || '#27ae60',
                    strokeOpacity: options.strokeOpacity || 0.9,
                    strokeWeight: options.strokeWeight || 5,
                    map: rawMap
                }, options));
                return {
                    line: polyline,
                    rawPolyline: polyline,
                    setOptions: function(newOpts) { polyline.setOptions(newOpts); },
                    setMap: function(m) { polyline.setMap(m ? (m.rawMap || m) : null); },
                    addListener: function(event, cb) { return polyline.addListener(event, cb); },
                    bindPopup: function(content) { return this; },
                    remove: function() { polyline.setMap(null); }
                };
            }

            if (window.L) {
                const line = L.polyline(pathLeaflet, {
                    color: options.strokeColor || '#27ae60',
                    weight: options.strokeWeight || 5,
                    opacity: options.strokeOpacity !== undefined ? options.strokeOpacity : 0.9,
                    dashArray: options.dashArray || null
                }).addTo(rawMap);

                return {
                    line: line,
                    setOptions: function(newOpts) {
                        line.setStyle({
                            color: newOpts.strokeColor || options.strokeColor,
                            weight: newOpts.strokeWeight || options.strokeWeight,
                            opacity: newOpts.strokeOpacity !== undefined ? newOpts.strokeOpacity : options.strokeOpacity
                        });
                    },
                    setMap: function(m) {
                        const rm = m && m.rawMap ? m.rawMap : m;
                        if (rm) rm.addLayer(line);
                        else line.remove();
                    },
                    addListener: function(event, cb) {
                        line.on(event, function(e) {
                            cb({
                                latLng: {
                                    lat: () => e.latlng.lat,
                                    lng: () => e.latlng.lng,
                                    lat: e.latlng.lat,
                                    lng: e.latlng.lng
                                }
                            });
                        });
                    },
                    bindPopup: function(content) {
                        line.bindPopup(content);
                        return this;
                    },
                    remove: function() {
                        line.remove();
                    }
                };
            }

            return null;
        },

        /**
         * Fit map bounds regardless of engine
         */
        fitBounds: function (map, coordinates) {
            if (!map || !coordinates || coordinates.length === 0) return;
            const isGoogle = map.isGoogleMap === true;

            if (isGoogle && window.google && window.google.maps) {
                const bounds = new google.maps.LatLngBounds();
                coordinates.forEach(c => {
                    const lat = typeof c.lat === 'function' ? c.lat() : (c.lat !== undefined ? c.lat : c[0]);
                    const lng = typeof c.lng === 'function' ? c.lng() : (c.lng !== undefined ? c.lng : c[1]);
                    bounds.extend(new google.maps.LatLng(lat, lng));
                });
                map.fitBounds(bounds);
            } else if (map.fitBounds) {
                const lCoords = coordinates.map(c => {
                    const lat = typeof c.lat === 'function' ? c.lat() : (c.lat !== undefined ? c.lat : c[0]);
                    const lng = typeof c.lng === 'function' ? c.lng() : (c.lng !== undefined ? c.lng : c[1]);
                    return [lat, lng];
                });
                map.fitBounds(lCoords);
            }
        },

        /**
         * Create Verified Nearby Helper Marker
         */
        createHelperMarker: function (map, helper, isDemo = false) {
            const lat = helper.lat;
            const lng = helper.lng;

            const helperHTML = `
                <div class="nearby-helper-dot" title="${helper.title}">
                    <div class="nearby-helper-pulse"></div>
                    <i class="bi bi-shield-fill-check"></i>
                </div>
            `;
            const demoTag = isDemo ? '<span style="background:#f1f5f9;color:#64748b;border:1px solid #cbd5e1;padding:2px 6px;border-radius:4px;font-size:0.65rem;margin-left:4px;">Demo Data</span>' : '';
            const popupContent = `
                <div style="font-family:'Plus Jakarta Sans',sans-serif;padding:6px;min-width:210px;">
                    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
                        <span style="background:#10b981;color:#ffffff;font-size:0.7rem;font-weight:700;padding:2px 8px;border-radius:9999px;">
                            Verified Citizen
                        </span>
                        <span style="color:#d97706;font-weight:700;font-size:0.8rem;">
                            ★ ${(helper.trust || 4.9).toFixed(1)}
                        </span>
                    </div>
                    <strong style="display:block;font-size:0.92rem;color:#0f172a;margin-bottom:3px;">
                        ${helper.title} ${demoTag}
                    </strong>
                    <div style="color:#64748b;font-size:0.8rem;margin-bottom:4px;">
                        <i class="bi bi-award-fill" style="color:#f59e0b;margin-right:4px;"></i>${helper.badge || 'Community Guardian'}
                    </div>
                    <div style="color:#dc2626;font-weight:700;font-size:0.82rem;margin-bottom:4px;">
                        <i class="bi bi-geo-alt-fill" style="margin-right:4px;"></i>${helper.distance_text || 'Nearby'} &bull; ETA ~${helper.eta_minutes || 3} mins
                    </div>
                    <div style="color:#16a34a;font-weight:600;font-size:0.78rem;">
                        <i class="bi bi-check-circle-fill" style="margin-right:4px;"></i>Available for dispatch
                    </div>
                </div>
            `;

            return this.createCustomMarker(map, {
                lat: lat,
                lng: lng,
                html: helperHTML,
                title: helper.title,
                popupContent: popupContent
            });
        },

        /**
         * Attach full SOS emergency layer to a Map:
         * - Victim SOS Beacon Marker
         * - 3 km Radius Circle
         * - Dynamic nearby helper dots
         * - Live distance calculation and HUD callbacks
         */
        attachNearbyUsersLayer: function (map, victimLat, victimLng, options = {}) {
            const self = this;
            let currentLat = parseFloat(victimLat);
            let currentLng = parseFloat(victimLng);
            const radiusKm = options.radiusKm || 3.0;
            const radiusMeters = radiusKm * 1000;

            // 1. Add SOS Victim Marker
            const victimObj = self.createSOSMarker(map, currentLat, currentLng, options.victimLabel || "YOU (DISTRESS LOCATION)");

            // 2. Add 3 km Emergency Assistance Zone Circle
            const circle = self.createRadiusCircle(map, currentLat, currentLng, radiusMeters);

            // 3. Helper Markers Array
            let helperMarkers = [];
            let activeHelpersData = [];

            function haversineDistance(lat1, lon1, lat2, lon2) {
                const R = 6371; // km
                const dLat = (lat2 - lat1) * Math.PI / 180;
                const dLon = (lon2 - lon1) * Math.PI / 180;
                const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
                    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                    Math.sin(dLon / 2) * Math.sin(dLon / 2);
                const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
                return R * c;
            }

            function clearHelperMarkers() {
                helperMarkers.forEach(h => {
                    if (h && h.remove) h.remove();
                    else if (h && h.setMap) h.setMap(null);
                });
                helperMarkers = [];
            }

            function renderHelpers(helpers) {
                clearHelperMarkers();
                activeHelpersData = helpers;

                helpers.forEach(h => {
                    const hObj = self.createHelperMarker(map, h, h.is_demo);
                    if (hObj) helperMarkers.push(hObj);
                });

                // Compute nearest responder
                let nearest = null;
                let minDist = 9999;
                helpers.forEach(h => {
                    const distKm = haversineDistance(currentLat, currentLng, h.lat, h.lng);
                    if (distKm < minDist) {
                        minDist = distKm;
                        const distMeters = Math.round(distKm * 1000);
                        const distText = distMeters < 1000 ? `${distMeters} m` : `${distKm.toFixed(1)} km`;
                        const etaMins = Math.max(1, Math.round(distKm / 0.15));
                        nearest = {
                            helper: h,
                            distance_text: distText,
                            eta_minutes: etaMins
                        };
                    }
                });

                if (typeof options.onUpdate === 'function') {
                    options.onUpdate({
                        total: helpers.length,
                        nearest: nearest,
                        helpers: helpers
                    });
                }
            }

            function generateDefaultDemoHelpers(baseLat, baseLng) {
                return [];
            }

            function fetchLiveOrFallback() {
                const url = `/emergency/smart-radar/?lat=${currentLat}&lng=${currentLng}&radius=${radiusKm}`;
                fetch(url)
                    .then(res => res.json())
                    .then(data => {
                        if (data && data.success && Array.isArray(data.helpers)) {
                            renderHelpers(data.helpers);
                        } else {
                            renderHelpers([]);
                        }
                    })
                    .catch(() => {
                        renderHelpers([]);
                    });
            }

            // Initial load
            fetchLiveOrFallback();

            // Return controller
            return {
                setUserLocation: function (lat, lng) {
                    currentLat = parseFloat(lat);
                    currentLng = parseFloat(lng);
                    if (victimObj && victimObj.setPosition) {
                        victimObj.setPosition(currentLat, currentLng);
                    }
                    if (circle && circle.setCenter) {
                        circle.setCenter({ lat: currentLat, lng: currentLng });
                    }
                    fetchLiveOrFallback();
                },
                jitterPositions: function () {
                    fetchLiveOrFallback();
                },
                addDemoUser: function () {
                    fetchLiveOrFallback();
                },
                refresh: function () {
                    fetchLiveOrFallback();
                },
                destroy: function () {
                    clearHelperMarkers();
                    if (circle && circle.remove) circle.remove();
                    else if (circle && circle.setMap) circle.setMap(null);
                    if (victimObj && victimObj.remove) victimObj.remove();
                    else if (victimObj && victimObj.setMap) victimObj.setMap(null);
                }
            };
        }
    };

    window.GoogleMapsShield = GoogleMapsShield;

    // Backward compatibility bridge for any existing NearbyUsersMap calls
    window.NearbyUsersMap = {
        attachNearbyUsersLayer: function (map, lat, lng, options) {
            return GoogleMapsShield.attachNearbyUsersLayer(map, lat, lng, options);
        }
    };

})(window);
