from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from .models import LocalResident, LocalResidentResponse
from .serializers import LocalResidentSerializer, LocalResidentResponseSerializer
from .services import LocalResidentService


class RegisterLocalResidentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        resident, created = LocalResident.objects.get_or_create(user=request.user)
        serializer = LocalResidentSerializer(resident, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'success': True, 'resident': serializer.data},
                            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
        return Response({'success': False, 'errors': serializer.errors}, status=400)


RegisterGuardianAPIView = RegisterLocalResidentAPIView


class NearbyLocalResidentsAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        lat = request.GET.get('lat')
        lng = request.GET.get('lng')
        radius = float(request.GET.get('radius', 3))

        if not lat or not lng:
            return Response({'success': False, 'message': 'lat and lng required'}, status=400)

        nearby = LocalResidentService.get_nearby(lat, lng, radius_km=radius)
        return Response({
            'residents': LocalResidentSerializer(nearby, many=True).data,
            'guardians': LocalResidentSerializer(nearby, many=True).data,  # backward compatibility
            'count': len(nearby)
        })


NearbyGuardiansAPIView = NearbyLocalResidentsAPIView


class AcknowledgeLocalResidentResponseAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, sos_id):
        from emergency.models import Emergency
        from emergency.services import EmergencyService

        try:
            resident = LocalResident.objects.get(user=request.user)
        except LocalResident.DoesNotExist:
            return Response({'success': False, 'message': 'User is not a registered Local Resident'}, status=403)

        try:
            emergency = Emergency.objects.get(pk=sos_id, status='ACTIVE')
        except Emergency.DoesNotExist:
            return Response({'success': False, 'message': 'Active emergency not found'}, status=404)

        resp, _ = LocalResidentResponse.objects.get_or_create(sos_event=emergency, resident=resident)
        resp.status = 'acknowledged'
        resp.acknowledged_at = timezone.now()
        resp.save()

        EmergencyService.accept_emergency(emergency, request.user)

        return Response({
            'success': True,
            'message': 'Response acknowledged. You are assigned as responder.',
            'response': LocalResidentResponseSerializer(resp).data
        })
