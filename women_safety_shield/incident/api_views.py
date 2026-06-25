from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import IncidentEvent, IncidentReport
from .serializers import IncidentEventSerializer, IncidentReportSerializer
from emergency.models import Emergency


class IncidentReportAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, emergency_id):
        try:
            emergency = Emergency.objects.get(pk=emergency_id, victim=request.user)
        except Emergency.DoesNotExist:
            return Response({'message': 'Not found'}, status=404)

        events = IncidentEvent.objects.filter(emergency=emergency)
        return Response({
            'emergency_id': emergency_id,
            'status': emergency.status,
            'created_at': emergency.created_at,
            'closed_at': emergency.closed_at,
            'duration_minutes': emergency.duration_minutes(),
            'events': IncidentEventSerializer(events, many=True).data,
        })
