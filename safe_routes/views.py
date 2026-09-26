import json
import urllib.request
import urllib.parse
from django.shortcuts import render
from .services import SafeRouteService
from safety_map.models import SafetyZone, SafetyReport
from community.models import TrustedContact


def _geocode_local_query(query, bias_lat, bias_lng):
    """Geocode a text query near bias_lat, bias_lng using Nominatim with viewbox."""
    try:
        url = (
            f"https://nominatim.openstreetmap.org/search?format=json&q={urllib.parse.quote(query)}"
            f"&viewbox={bias_lng-0.4},{bias_lat+0.4},{bias_lng+0.4},{bias_lat-0.4}&bounded=0&limit=1"
        )
        req = urllib.request.Request(url, headers={'User-Agent': 'WomenSafetyShield/2.0'})
        with urllib.request.urlopen(req, timeout=3.5) as res:
            data = json.loads(res.read().decode())
            if data and len(data) > 0:
                return float(data[0]['lat']), float(data[0]['lon']), data[0]['display_name']
    except Exception:
        pass
    return None


def compare_routes_view(request):
    source = request.GET.get('source', '').strip()
    destination = request.GET.get('destination', '').strip()

    start_lat = request.GET.get('start_lat', '').strip()
    start_lng = request.GET.get('start_lng', '').strip()
    end_lat = request.GET.get('end_lat', '').strip()
    end_lng = request.GET.get('end_lng', '').strip()
    mode = request.GET.get('mode', 'walking').strip()

    default_lat, default_lng = 28.4744, 77.5039
    default_source = "KCC Institute, Knowledge Park III, Greater Noida"
    default_dest = "Pari Chowk Metro Station, Greater Noida"

    # 1. Parse start coords
    try:
        s_lat = float(start_lat)
        s_lng = float(start_lng)
    except (ValueError, TypeError):
        s_lat, s_lng = default_lat, default_lng
        start_lat, start_lng = str(default_lat), str(default_lng)
        source = source or default_source

    # 2. Parse or resolve end coords
    resolved_e_lat, resolved_e_lng = None, None
    try:
        test_e_lat = float(end_lat)
        test_e_lng = float(end_lng)
        dist_check = SafeRouteService._haversine(s_lat, s_lng, test_e_lat, test_e_lng)
        if dist_check < 120:
            resolved_e_lat, resolved_e_lng = test_e_lat, test_e_lng
    except (ValueError, TypeError):
        pass

    if resolved_e_lat is None:
        if destination:
            local_geo = _geocode_local_query(destination, s_lat, s_lng)
            if local_geo:
                resolved_e_lat, resolved_e_lng, full_name = local_geo
        if resolved_e_lat is None:
            resolved_e_lat = s_lat - 0.015
            resolved_e_lng = s_lng + 0.018
            destination = destination or default_dest

    e_lat, e_lng = resolved_e_lat, resolved_e_lng
    end_lat, end_lng = str(round(e_lat, 5)), str(round(e_lng, 5))

    routes = SafeRouteService.compare_routes(s_lat, s_lng, e_lat, e_lng, mode=mode)

    # 3. Community Safety Intelligence: Zones & Incident Reports
    zones = list(SafetyZone.objects.values('id', 'name', 'latitude', 'longitude', 'radius_meters', 'status'))
    
    reports_qs = SafetyReport.objects.select_related('user').order_by('-created_at')[:30]
    reports_list = []
    for r in reports_qs:
        reports_list.append({
            'id': r.id,
            'category': r.category,
            'category_display': r.get_category_display(),
            'location_name': r.location_name or 'Pinned Location',
            'description': r.description or '',
            'latitude': r.latitude,
            'longitude': r.longitude,
            'is_anonymous': r.is_anonymous,
            'reporter': 'Anonymous' if r.is_anonymous else r.user.username,
            'created_at': r.created_at.strftime('%d %b %H:%M'),
            'upvotes': r.upvotes,
        })

    if request.user.is_authenticated:
        trusted_contacts = TrustedContact.objects.filter(user=request.user, is_active=True).select_related('contact')
    else:
        trusted_contacts = []

    context = {
        'source': source,
        'destination': destination,
        'routes': routes,
        'routes_json': json.dumps(routes),
        'zones_json': json.dumps(zones),
        'reports_json': json.dumps(reports_list),
        'reports': reports_list,
        'start_lat': start_lat,
        'start_lng': start_lng,
        'end_lat': end_lat,
        'end_lng': end_lng,
        'mode': mode,
        'trusted_contacts': trusted_contacts,
        'categories': SafetyReport.CATEGORY_CHOICES,
    }
    return render(request, 'safe_routes/compare.html', context)
