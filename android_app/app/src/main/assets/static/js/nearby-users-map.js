/**
 * Women Safety Shield - Shared Nearby Users Map Helper
 * Implements consistent victim marker, 3 km assistance zone radius,
 * and nearby available-user dots/markers with demo simulation across all maps.
 */

(function (window) {
    'use strict';

    const NearbyUsersMap = {
        // Preset test/demo roles for realistic simulation
        DEMO_ROLES: [
            { title: "Aadhaar Verified Resident", badge: "Community Guardian", type: "Volunteer", trust: 4.9 },
            { title: "Campus Safety Marshal", badge: "First Responder", type: "Security Staff", trust: 5.0 },
            { title: "Women Safety Mitra", badge: "Neighborhood Watch", type: "Volunteer", trust: 4.8 },
            { title: "Emergency First Aider", badge: "Medical First Aid", type: "Citizen", trust: 4.9 },
            { title: "Resident Welfare Volunteer", badge: "Safe Haven Host", type: "Volunteer", trust: 4.7 },
            { title: "Verified Night Patrol", badge: "Rapid Patrol", type: "Security Staff", trust: 4.9 },
            { title: "Youth Safety Volunteer", badge: "Community Helper", type: "Citizen", trust: 4.8 },
            { title: "Transit Safety Escort", badge: "Verified Escort", type: "Volunteer", trust: 5.0 },
            { title: "Local Store Safe Haven", badge: "Safe Zone Merchant", type: "NGO Member", trust: 4.9 },
            { title: "Aadhaar Verified Protector", badge: "Shield Responder", type: "Volunteer", trust: 4.8 },
            { title: "Civic Safety Partner", badge: "Active Volunteer", type: "Citizen", trust: 4.9 },
            { title: "Certified Rescue Volunteer", badge: "Disaster Response", type: "Volunteer", trust: 5.0 }
        ],

        /**
         * Create distinct victim / user distress beacon marker
         */
        createVictimMarker: function (lat, lng, label = "YOU (DISTRESS LOCATION)") {
            const victimIcon = L.divIcon({
                className: 'sos-beacon-wrapper',
                html: `
                    <div class="sos-pulse-beacon" title="${label}">
                        <div class="sos-beacon-ring"></div>
                        <div class="sos-beacon-ring ring-2"></div>
                        <div class="sos-beacon-core"><i class="bi bi-exclamation-triangle-fill"></i></div>
                    </div>
                `,
                iconSize: [36, 36],
                iconAnchor: [18, 18]
            });

            const marker = L.marker([lat, lng], { icon: victimIcon, zIndexOffset: 2000 });
            marker.bindPopup(`
                <div class="p-1 text-center" style="font-family:'Plus Jakarta Sans',sans-serif;min-width:180px;">
                    <strong class="text-danger d-block fs-6 mb-1">
                        <i class="bi bi-exclamation-octagon-fill me-1"></i>${label}
                    </strong>
                    <div class="small text-muted mb-1">GPS: ${lat.toFixed(4)}, ${lng.toFixed(4)}</div>
                    <span class="badge bg-danger text-white rounded-2 px-2">Distress Active</span>
                </div>
            `);
            return marker;
        },

        /**
         * Create clear 3 km emergency assistance zone circle
         */
        createRadiusCircle: function (lat, lng, radiusMeters = 3000, options = {}) {
            const defaults = {
                radius: radiusMeters,
                color: '#dc2626',
                fillColor: '#ef4444',
                fillOpacity: 0.12,
                weight: 2,
                dashArray: '6, 6'
            };
            const circle = L.circle([lat, lng], Object.assign({}, defaults, options));
            circle.bindTooltip(`${(radiusMeters / 1000).toFixed(1)} KM EMERGENCY ASSISTANCE ZONE`, {
                permanent: false,
                direction: 'top'
            });
            return circle;
        },

        /**
         * Create nearby available-user dot/marker
         */
        createHelperMarker: function (helper) {
            const isDemo = helper.is_real === false || helper.is_demo !== false;
            const dotIcon = L.divIcon({
                className: 'nearby-helper-marker',
                html: `
                    <div class="nearby-helper-dot" title="${helper.title}">
                        <div class="nearby-helper-pulse"></div>
                        <i class="bi bi-shield-fill-check"></i>
                    </div>
                `,
                iconSize: [26, 26],
                iconAnchor: [13, 13]
            });

            const marker = L.marker([helper.lat, helper.lng], { icon: dotIcon, zIndexOffset: 500 });
            const demoTag = isDemo ? '<span class="badge bg-secondary-subtle text-secondary border ms-1" style="font-size:0.65rem;">Demo Data</span>' : '';

            marker.bindPopup(`
                <div style="min-width:220px;font-family:'Plus Jakarta Sans',sans-serif;padding:2px;">
                    <div class="d-flex align-items-center justify-content-between mb-1">
                        <div class="d-flex align-items-center">
                            <span class="badge bg-success text-white" style="font-size:0.7rem;">Verified User</span>
                            ${demoTag}
                        </div>
                        <small class="text-warning fw-bold"><i class="bi bi-star-fill me-1"></i>${Number(helper.trust_score || 4.9).toFixed(1)}</small>
                    </div>
                    <strong class="d-block mb-1" style="font-size:0.88rem;color:#1e293b;">${helper.title}</strong>
                    <div class="small text-muted mb-1"><i class="bi bi-award-fill text-warning me-1"></i>${helper.badge || 'Community Guardian'}</div>
                    <div class="small fw-bold text-danger mb-1">
                        <i class="bi bi-geo-alt-fill me-1"></i>${helper.distance_text || (helper.distance_km ? helper.distance_km + ' km' : '~500m')} away &bull; ETA ~${helper.eta_minutes || 3} mins
                    </div>
                    <div class="small text-success fw-semibold"><i class="bi bi-check-circle-fill me-1"></i>${helper.status || 'Available & On Standby'}</div>
                </div>
            `);
            return marker;
        },

        /**
         * Generate simulated demo helpers around given coordinates within radius
         */
        generateDemoHelpers: function (centerLat, centerLng, count = 12, radiusKm = 3.0) {
            const helpers = [];
            for (let i = 0; i < count; i++) {
                const role = this.DEMO_ROLES[i % this.DEMO_ROLES.length];
                const angle = Math.random() * 2 * Math.PI;
                // Distributed smoothly within 250m to 90% of radius
                const dist = 0.25 + Math.random() * (radiusKm * 0.9 - 0.25);
                const deltaLat = (dist / 111.0) * Math.cos(angle);
                const deltaLng = (dist / (111.0 * Math.cos(centerLat * Math.PI / 180))) * Math.sin(angle);

                const dCalc = Math.round(dist * 100) / 100;
                const dText = dCalc < 1.0 ? `${Math.round(dCalc * 1000)} m` : `${dCalc.toFixed(1)} km`;
                const etaMin = Math.max(1, Math.round((dCalc / 4.5) * 60));

                helpers.push({
                    id: `demo_user_${i + 1}`,
                    title: role.title,
                    badge: role.badge,
                    type: role.type,
                    lat: centerLat + deltaLat,
                    lng: centerLng + deltaLng,
                    distance_km: dCalc,
                    distance_text: dText,
                    eta_minutes: etaMin,
                    trust_score: role.trust,
                    is_real: false,
                    is_demo: true,
                    status: "Available & On Standby"
                });
            }
            helpers.sort((a, b) => a.distance_km - b.distance_km);
            return helpers;
        },

        /**
         * Standard helper to mount victim marker, 3km radius, and nearby-user dots onto ANY Google Map or Leaflet map
         */
        attachNearbyUsersLayer: function (map, userLat, userLng, options = {}) {
            if (window.google && window.google.maps && ((typeof google.maps.Map === 'function' && map instanceof google.maps.Map) || (map && map.setCenter && !map.setView))) {
                if (window.GoogleMapsShield) {
                    return window.GoogleMapsShield.attachNearbyUsersLayer(map, userLat, userLng, options);
                }
            }

            const radiusKm = options.radiusKm || 3.0;
            const onUpdate = options.onUpdate || null;
            const useApi = options.useApi !== false;

            // 1. Victim Marker
            const victimMarker = this.createVictimMarker(userLat, userLng, options.victimLabel || "YOU (DISTRESS LOCATION)");
            victimMarker.addTo(map);

            // 2. 3 km Zone
            const zoneCircle = this.createRadiusCircle(userLat, userLng, radiusKm * 1000);
            zoneCircle.addTo(map);

            // 3. Helpers Layer Group
            const helpersLayer = L.layerGroup().addTo(map);
            let currentHelpers = [];

            // Function to render helper dots
            const renderHelpers = (helpers) => {
                helpersLayer.clearLayers();
                currentHelpers = helpers;
                helpers.forEach(h => {
                    const marker = this.createHelperMarker(h);
                    helpersLayer.addLayer(marker);
                });
                if (typeof onUpdate === 'function') {
                    onUpdate({
                        total: helpers.length,
                        nearest: helpers[0] || null,
                        helpers: helpers,
                        radiusKm: radiusKm
                    });
                }
            };

            // Fetch from API (only real verified responders from database)
            const fetchOrGenerate = () => {
                if (useApi) {
                    fetch(`/emergency/smart-radar/?lat=${userLat}&lng=${userLng}&radius=${radiusKm}`)
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
                } else {
                    renderHelpers([]);
                }
            };

            fetchOrGenerate();

            // Return controller object for dynamic updates
            return {
                victimMarker,
                zoneCircle,
                helpersLayer,
                getHelpers: () => currentHelpers,
                refresh: fetchOrGenerate,
                setUserLocation: (newLat, newLng) => {
                    userLat = newLat;
                    userLng = newLng;
                    victimMarker.setLatLng([newLat, newLng]);
                    zoneCircle.setLatLng([newLat, newLng]);
                    fetchOrGenerate();
                },
                // Simulation controls for testing (Requirement 6)
                addDemoUser: () => {
                    const role = NearbyUsersMap.DEMO_ROLES[Math.floor(Math.random() * NearbyUsersMap.DEMO_ROLES.length)];
                    const angle = Math.random() * 2 * Math.PI;
                    const dist = 0.3 + Math.random() * (radiusKm * 0.85);
                    const deltaLat = (dist / 111.0) * Math.cos(angle);
                    const deltaLng = (dist / (111.0 * Math.cos(userLat * Math.PI / 180))) * Math.sin(angle);
                    const dCalc = Math.round(dist * 100) / 100;

                    const newHelper = {
                        id: `demo_user_${Date.now()}`,
                        title: role.title,
                        badge: role.badge,
                        type: role.type,
                        lat: userLat + deltaLat,
                        lng: userLng + deltaLng,
                        distance_km: dCalc,
                        distance_text: dCalc < 1.0 ? `${Math.round(dCalc * 1000)} m` : `${dCalc.toFixed(1)} km`,
                        eta_minutes: Math.max(1, Math.round((dCalc / 4.5) * 60)),
                        trust_score: role.trust,
                        is_real: false,
                        is_demo: true,
                        status: "Available & On Standby"
                    };

                    currentHelpers.push(newHelper);
                    currentHelpers.sort((a, b) => a.distance_km - b.distance_km);
                    renderHelpers(currentHelpers);
                },
                removeDemoUser: () => {
                    if (currentHelpers.length > 1) {
                        currentHelpers.pop();
                        renderHelpers(currentHelpers);
                    }
                },
                jitterPositions: () => {
                    currentHelpers.forEach(h => {
                        h.lat += (Math.random() - 0.5) * 0.0006;
                        h.lng += (Math.random() - 0.5) * 0.0006;
                    });
                    renderHelpers(currentHelpers);
                }
            };
        }
    };

    window.NearbyUsersMap = NearbyUsersMap;
})(window);
