from .models import Guardian


def get_nearby_guardians(lat, lng, radius_km=3):
    import math
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = math.sin(d_lat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon/2)**2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    guardians = Guardian.objects.filter(is_verified=True, is_available=True).select_related('user')
    nearby = []
    for g in guardians:
        if g.latitude and g.longitude:
            dist = haversine(float(lat), float(lng), float(g.latitude), float(g.longitude))
            if dist <= radius_km:
                g.distance_km = round(dist, 2)
                nearby.append(g)
    return sorted(nearby, key=lambda g: (g.distance_km, -g.trust_score))
