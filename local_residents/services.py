import math
from .models import LocalResident


class LocalResidentService:
    @staticmethod
    def get_nearby(lat, lng, radius_km=3):
        """Find verified, available local residents within radius_km."""
        if LocalResident.objects.filter(is_verified=True).count() < 6:
            try:
                from .seed_data import seed_verified_residents
                seed_verified_residents()
            except Exception:
                pass

        residents = LocalResident.objects.filter(is_verified=True, is_available=True).select_related('user')
        nearby = []
        for r in residents:
            if r.latitude and r.longitude:
                dist = LocalResidentService._haversine(float(lat), float(lng), float(r.latitude), float(r.longitude))
                if dist <= radius_km:
                    r.distance_km = round(dist, 2)
                    nearby.append(r)
        nearby.sort(key=lambda x: (x.distance_km, -x.trust_score))
        return nearby

    @staticmethod
    def _haversine(lat1, lon1, lat2, lon2):
        R = 6371
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = math.sin(d_lat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c
