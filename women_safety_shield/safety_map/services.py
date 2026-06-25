from .models import SafetyZone, SafetyReport


def get_area_risk_score(lat, lng, radius_km=0.5):
    import math
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = math.sin(d_lat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon/2)**2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    reports = SafetyReport.objects.all()
    nearby_bad = 0
    nearby_good = 0
    for r in reports:
        dist = haversine(lat, lng, r.latitude, r.longitude)
        if dist <= radius_km:
            if r.category == 'safe':
                nearby_good += 1
            else:
                nearby_bad += 1

    total = nearby_bad + nearby_good
    if total == 0:
        return 5.0
    return round((nearby_bad / total) * 10, 1)
