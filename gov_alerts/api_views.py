from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import GovAlert
from .services import GovAlertService


class TriggerGovAlertAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, sos_id):
        from emergency.models import Emergency
        emergency = get_object_or_404(Emergency, pk=sos_id)
        is_authorized = (
            emergency.victim == request.user or
            emergency.assigned_responder == request.user or
            request.user in emergency.notified_contacts.all() or
            getattr(request.user, 'role', '') in ('police', 'admin') or
            request.user.is_staff or request.user.is_superuser
        )
        if not is_authorized:
            return Response({'success': False, 'message': 'Permission denied'}, status=403)

        channel = request.data.get('channel', '112_ERSS')
        alert = GovAlertService.trigger_emergency_alert(emergency, channel=channel)
        return Response({
            'success': True,
            'alert_id': alert.id,
            'channel': alert.channel,
            'delivery_status': alert.delivery_status
        })


class GovAlertStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, sos_id):
        from emergency.models import Emergency
        emergency = get_object_or_404(Emergency, pk=sos_id)
        is_authorized = (
            emergency.victim == request.user or
            emergency.assigned_responder == request.user or
            request.user in emergency.notified_contacts.all() or
            getattr(request.user, 'role', '') in ('police', 'admin') or
            request.user.is_staff or request.user.is_superuser
        )
        if not is_authorized:
            return Response({'success': False, 'message': 'Permission denied'}, status=403)

        alerts = GovAlert.objects.filter(sos_event_id=sos_id).order_by('-sent_at')
        return Response({
            'success': True,
            'alerts': [
                {
                    'id': a.id,
                    'channel': a.channel,
                    'sent_at': a.sent_at,
                    'delivery_status': a.delivery_status,
                    'payload': a.response_payload
                }
                for a in alerts
            ]
        })
