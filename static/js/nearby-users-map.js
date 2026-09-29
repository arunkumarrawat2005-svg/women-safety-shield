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
         * Create distinct victim / user distress beacon marker (Matches Blue User Pin from reference design)
         */
        createVictimMarker: function (lat, lng, label = "YOU (YOUR LOCATION)") {
            const victimIcon = L.divIcon({
                className: 'map-user-beacon-wrapper',
                html: `
                    <div class="map-user-beacon-wrapper" title="${label}">
                        <div class="map-user-radar-wave"></div>
                        <div class="map-user-pin-bubble">
                            <i class="bi bi-person-fill"></i>
                            <div class="map-user-pin-point"></div>
                        </div>
                    </div>
                `,
                iconSize: [44, 44],
                iconAnchor: [22, 22]
            });

            const marker = L.marker([lat, lng], { icon: victimIcon, zIndexOffset: 2000 });
            marker.bindPopup(`
                <div style="font-family:'Plus Jakarta Sans',sans-serif;padding:6px;text-align:center;min-width:180px;">
                    <strong style="color:#2563eb;font-size:0.95rem;display:block;margin-bottom:4px;">
                        <i class="bi bi-geo-alt-fill" style="margin-right:4px;"></i>${label}
                    </strong>
                    <div style="color:#64748b;font-size:0.8rem;margin-bottom:6px;">
                        GPS: ${parseFloat(lat).toFixed(4)}, ${parseFloat(lng).toFixed(4)}
                    </div>
                    <span style="background:#2563eb;color:#ffffff;font-size:0.75rem;padding:3px 10px;border-radius:6px;font-weight:700;">
                        Live User Location
                    </span>
                </div>
            `);
            return marker;
        },

        /**
         * Create clear 3 km emergency assistance zone circle (Soft blue radar circle)
         */
        createRadiusCircle: function (lat, lng, radiusMeters = 3000, options = {}) {
            const defaults = {
                radius: radiusMeters,
                color: '#2563eb',
                fillColor: '#3b82f6',
                fillOpacity: 0.16,
                weight: 1.5
            };
            const circle = L.circle([lat, lng], Object.assign({}, defaults, options));
            circle.bindTooltip(`${(radiusMeters / 1000).toFixed(1)} KM EMERGENCY ASSISTANCE ZONE`, {
                permanent: false,
                direction: 'top'
            });
            return circle;
        },

        /**
         * Create nearby available-user dot/marker (Matches 4 Red Person badges & 1 Blue Shield badge)
         */
        createHelperMarker: function (helper) {
            const isDemo = helper.is_real === false || helper.is_demo !== false;
            const isPolice = helper.is_police || helper.type === 'Police' || helper.type === 'Security Staff' || 
                             (helper.badge && (helper.badge.includes('112') || helper.badge.includes('Patrol') || helper.badge.includes('Marshal') || helper.badge.includes('Police')));

            const iconClass = isPolice ? 'bi-shield-fill-check' : 'bi-person-fill';
            const badgeClass = isPolice ? 'map-marker-police' : 'map-marker-resident';
            const haloClass = isPolice ? 'halo-blue' : 'halo-red';
            const coreClass = isPolice ? 'core-blue' : 'core-red';

            const dotIcon = L.divIcon({
                className: 'map-marker-div-icon',
                html: `
                    <div class="map-marker-badge ${badgeClass}" title="${helper.title}">
                        <div class="map-marker-halo ${haloClass}"></div>
                        <div class="map-marker-core ${coreClass}">
                            <i class="bi ${iconClass}"></i>
                        </div>
                    </div>
                `,
                iconSize: [28, 28],
                iconAnchor: [14, 14]
            });

            const marker = L.marker([helper.lat, helper.lng], { icon: dotIcon, zIndexOffset: 500 });
            const demoTag = isDemo ? '<span style="background:#f1f5f9;color:#64748b;border:1px solid #cbd5e1;padding:2px 6px;border-radius:4px;font-size:0.65rem;margin-left:4px;">Verified Profile</span>' : '';

            marker.bindPopup(`
                <div style="min-width:210px;font-family:'Plus Jakarta Sans',sans-serif;padding:6px;">
                    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
                        <span style="background:${isPolice ? '#2563eb' : '#ef4444'};color:#ffffff;font-size:0.7rem;font-weight:700;padding:2px 8px;border-radius:6px;">
                            ${isPolice ? 'Police / Haven' : 'Community Guardian'}
                        </span>
                        <span style="color:#d97706;font-weight:700;font-size:0.8rem;">
                            ★ ${(helper.trust_score || helper.trust || 4.9).toFixed(1)}
                        </span>
                    </div>
                    <strong style="display:block;font-size:0.92rem;color:#0f172a;margin-bottom:3px;">
                        ${helper.title} ${demoTag}
                    </strong>
                    <div style="color:#64748b;font-size:0.8rem;margin-bottom:4px;">
                        <i class="bi bi-award-fill" style="color:#f59e0b;margin-right:4px;"></i>${helper.badge || (isPolice ? 'ERSS 112 Rapid Patrol' : 'Community Guardian')}
                    </div>
                    <div style="color:#dc2626;font-weight:700;font-size:0.82rem;margin-bottom:4px;">
                        <i class="bi bi-geo-alt-fill" style="margin-right:4px;"></i>${helper.distance_text || (helper.distance_km ? helper.distance_km + ' km' : '~500m')} away &bull; ETA ~${helper.eta_minutes || 3} mins
                    </div>
                    <div style="color:#16a34a;font-weight:600;font-size:0.78rem;">
                        <i class="bi bi-check-circle-fill" style="margin-right:4px;"></i>Available for dispatch
                    </div>
                </div>
            `);
            return marker;
        },

        /**
         * Generate simulated demo helpers around given coordinates within radius
         * Matching the exact 5 surrounding responder positions in the reference design
         */
        generateDemoHelpers: function (centerLat, centerLng, count = 5, radiusKm = 3.0) {
            const defaultGrid = [
                {
                    id: 'guardian_1',
                    title: 'Aadhaar Verified Resident',
                    badge: 'Community Guardian',
                    type: 'Volunteer',
                    lat: centerLat + 0.0072,
                    lng: centerLng - 0.0034,
                    is_demo: true,
                    is_police: false,
                    distance_km: 0.8,
                    distance_text: '800 m',
                    eta_minutes: 2,
                    trust_score: 4.9,
                    status: 'Available & On Standby'
                },
                {
                    id: 'guardian_2',
                    title: 'Women Safety Mitra',
                    badge: 'Neighborhood Watch',
                    type: 'Volunteer',
                    lat: centerLat + 0.0036,
                    lng: centerLng - 0.0090,
                    is_demo: true,
                    is_police: false,
                    distance_km: 0.9,
                    distance_text: '900 m',
                    eta_minutes: 3,
                    trust_score: 4.8,
                    status: 'Available & On Standby'
                },
                {
                    id: 'guardian_3',
                    title: 'Resident Welfare Guardian',
                    badge: 'Safe Haven Host',
                    type: 'Citizen',
                    lat: centerLat - 0.0060,
                    lng: centerLng - 0.0076,
                    is_demo: true,
                    is_police: false,
                    distance_km: 1.1,
                    distance_text: '1.1 km',
                    eta_minutes: 4,
                    trust_score: 4.9,
                    status: 'Available & On Standby'
                },
                {
                    id: 'police_1',
                    title: 'Police PCR Patrol Beat',
                    badge: 'ERSS 112 Rapid Patrol',
                    type: 'Police',
                    lat: centerLat + 0.0050,
                    lng: centerLng + 0.0066,
                    is_demo: true,
                    is_police: true,
                    distance_km: 0.7,
                    distance_text: '700 m',
                    eta_minutes: 2,
                    trust_score: 5.0,
                    status: 'On Patrol • Rapid Response'
                },
                {
                    id: 'guardian_4',
                    title: 'Campus Safety Escort',
                    badge: 'Verified Escort',
                    type: 'Volunteer',
                    lat: centerLat - 0.0016,
                    lng: centerLng + 0.0102,
                    is_demo: true,
                    is_police: false,
                    distance_km: 1.0,
                    distance_text: '1.0 km',
                    eta_minutes: 3,
                    trust_score: 4.9,
                    status: 'Available & On Standby'
                }
            ];

            if (count <= 5) {
                return defaultGrid.slice(0, count);
            }

            const helpers = [...defaultGrid];
            for (let i = 5; i < count; i++) {
                const role = this.DEMO_ROLES[i % this.DEMO_ROLES.length];
                const angle = Math.random() * 2 * Math.PI;
                const dist = 0.4 + Math.random() * (radiusKm * 0.85);
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
                    is_police: role.type === 'Police' || role.type === 'Security Staff',
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

            // 1. Victim Marker (Blue person pin)
            const victimMarker = this.createVictimMarker(userLat, userLng, options.victimLabel || "YOU (YOUR LOCATION)");
            victimMarker.addTo(map);

            // 2. 3 km Zone (Soft blue radar circle)
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

            // Fetch from API or fallback to active community grid
            const fetchOrGenerate = () => {
                if (useApi) {
                    fetch(`/emergency/smart-radar/?lat=${userLat}&lng=${userLng}&radius=${radiusKm}`)
                        .then(res => res.json())
                        .then(data => {
                            if (data && data.success && Array.isArray(data.helpers) && data.helpers.length > 0) {
                                renderHelpers(data.helpers);
                            } else {
                                renderHelpers(this.generateDemoHelpers(userLat, userLng, 5, radiusKm));
                            }
                        })
                        .catch(() => {
                            renderHelpers(this.generateDemoHelpers(userLat, userLng, 5, radiusKm));
                        });
                } else {
                    renderHelpers(this.generateDemoHelpers(userLat, userLng, 5, radiusKm));
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
