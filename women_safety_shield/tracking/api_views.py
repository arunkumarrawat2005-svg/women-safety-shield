from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Location
from .serializers import LocationSerializer


class UpdateLocationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data.copy()
        data['user'] = request.user.id
        serializer = LocationSerializer(data=data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response({'success': True, 'location': serializer.data})
        return Response({'success': False, 'errors': serializer.errors}, status=400)


class LocationHistoryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        locations = Location.objects.filter(user=request.user).order_by('-timestamp')[:50]
        return Response({'locations': LocationSerializer(locations, many=True).data})
