from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import Emergency
from .serializers import EmergencySerializer, CreateEmergencySerializer
from .services import EmergencyService


class CreateEmergencyAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateEmergencySerializer(data=request.data)
        if serializer.is_valid():
            emergency = EmergencyService.create_emergency(
                user=request.user,
                latitude=serializer.validated_data['latitude'],
                longitude=serializer.validated_data['longitude'],
                trigger_type=serializer.validated_data.get('trigger_type', 'button'),
                description=serializer.validated_data.get('description', '')
            )
            return Response({
                'success': True,
                'emergency': EmergencySerializer(emergency).data,
                'message': 'SOS activated. Help is on the way!'
            }, status=status.HTTP_201_CREATED)
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class EmergencyStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        emergencies = Emergency.objects.filter(victim=request.user).order_by('-created_at')[:5]
        return Response({'emergencies': EmergencySerializer(emergencies, many=True).data})


class AcceptEmergencyAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            emergency = Emergency.objects.get(pk=pk, status='ACTIVE')
            EmergencyService.accept_emergency(emergency, request.user)
            return Response({'success': True, 'message': 'Emergency accepted'})
        except Emergency.DoesNotExist:
            return Response({'success': False, 'message': 'Emergency not found'}, status=404)


class CloseEmergencyAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            emergency = Emergency.objects.get(pk=pk, victim=request.user)
            EmergencyService.close_emergency(emergency)
            return Response({'success': True, 'message': 'Emergency closed'})
        except Emergency.DoesNotExist:
            return Response({'success': False, 'message': 'Emergency not found'}, status=404)
