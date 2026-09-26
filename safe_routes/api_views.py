from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .services import SafeRouteService


class SafeRoutesCompareAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from_coords = request.GET.get('from', '')
        to_coords = request.GET.get('to', '')

        if not from_coords or not to_coords:
            return Response({'success': False, 'message': 'Both from and to query params required (lat,lng)'}, status=400)

        try:
            start_lat, start_lng = map(float, from_coords.split(','))
            end_lat, end_lng = map(float, to_coords.split(','))
        except (ValueError, TypeError):
            return Response({'success': False, 'message': 'Invalid lat,lng format'}, status=400)

        routes = SafeRouteService.compare_routes(start_lat, start_lng, end_lat, end_lng)
        return Response({
            'success': True,
            'notice': 'Predicted AI scores for comparative decision. Not an absolute safety guarantee.',
            'candidate_routes': routes
        })


class SegmentScoreAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        lat = request.GET.get('lat')
        lng = request.GET.get('lng')

        if not lat or not lng:
            return Response({'success': False, 'message': 'lat and lng query params required'}, status=400)

        score, factors = SafeRouteService.score_point(float(lat), float(lng))
        return Response({
            'success': True,
            'latitude': float(lat),
            'longitude': float(lng),
            'predicted_safety_score': score,
            'risk_factors': factors
        })
