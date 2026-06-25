from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import Guardian
from .serializers import GuardianSerializer


class RegisterGuardianAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        guardian, created = Guardian.objects.get_or_create(user=request.user)
        serializer = GuardianSerializer(guardian, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'success': True, 'guardian': serializer.data},
                            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
        return Response({'success': False, 'errors': serializer.errors}, status=400)


class NearbyGuardiansAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        lat = request.GET.get('lat')
        lng = request.GET.get('lng')
        radius = float(request.GET.get('radius', 3))

        if not lat or not lng:
            return Response({'success': False, 'message': 'lat and lng required'}, status=400)

        from emergency.models import Emergency
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
                if dist <= radius:
                    g.distance_km = round(dist, 2)
                    nearby.append(g)

        nearby.sort(key=lambda g: (g.distance_km, -g.trust_score))
        return Response({'guardians': GuardianSerializer(nearby, many=True).data, 'count': len(nearby)})
