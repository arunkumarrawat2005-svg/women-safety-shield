from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied

from emergency.models import Emergency
from .models import IncidentRecord
from .services import IncidentRecordService


class RecordBreadcrumbAPIView(APIView):
    """
    Feature 1 & Feature 3:
    Append-only GPS breadcrumb reporting endpoint for active responders.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        lat = request.data.get('latitude')
        lng = request.data.get('longitude')
        emergency_id = request.data.get('emergency_id')
        accuracy = request.data.get('accuracy')
        speed = request.data.get('speed')

        if lat is None or lng is None:
            return Response({'success': False, 'error': 'Latitude and longitude are required.'}, status=400)

        result = IncidentRecordService.record_location_breadcrumb(
            responder_user=request.user,
            latitude=float(lat),
            longitude=float(lng),
            emergency_id=emergency_id,
            accuracy=float(accuracy) if accuracy is not None else None,
            speed=float(speed) if speed is not None else None,
        )

        if not result:
            return Response({'success': False, 'error': 'No active dispatch record found for this responder.'}, status=404)

        return Response({
            'success': True,
            'distance_meters': round(result['distance_meters'], 1),
            'arrived': result['arrived'],
            'arrival_triggered': result['arrival_triggered'],
            'status': result['record'].status,
        })


class IncidentRecordStatusAPIView(APIView):
    """
    Feature 4: Masked victim-facing responder status endpoint.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, sos_id):
        emergency = get_object_or_404(Emergency, pk=sos_id)
        info = IncidentRecordService.get_masked_responder_info(emergency, request.user)
        if not info:
            return Response({'success': False, 'dispatched': False})

        record = info.get('record')
        latest_breadcrumb = record.breadcrumbs.order_by('-timestamp').first()

        return Response({
            'success': True,
            'dispatched': True,
            'is_masked': info.get('is_masked', True),
            'responder_name': info.get('name'),
            'responder_label': info.get('label'),
            'responder_phone': info.get('phone'),
            'arrived': record.is_arrival_detected,
            'arrival_at': record.arrival_at,
            'status': record.status,
            'reveal_status': info.get('reveal_status'),
            'latest_location': {
                'latitude': latest_breadcrumb.latitude if latest_breadcrumb else None,
                'longitude': latest_breadcrumb.longitude if latest_breadcrumb else None,
                'timestamp': latest_breadcrumb.timestamp if latest_breadcrumb else None,
            } if latest_breadcrumb else None,
        })


class AdminUnmaskIdentityAPIView(APIView):
    """
    Feature 5: Scoped API endpoint to unmask responder identity with mandatory audit reason.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, record_id):
        record = get_object_or_404(IncidentRecord, pk=record_id)
        reason = request.data.get('access_reason', '').strip()

        if not reason or len(reason) < 5:
            return Response({'success': False, 'error': 'A detailed legal / investigation reason is required.'}, status=400)

        try:
            ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '127.0.0.1'))
            if ',' in ip:
                ip = ip.split(',')[0].strip()
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            audit = IncidentRecordService.log_admin_identity_access(
                admin_user=request.user,
                incident_record=record,
                reason=reason,
                ip_address=ip,
                user_agent=user_agent
            )
            return Response({
                'success': True,
                'audit_id': audit.id,
                'responder': {
                    'id': record.responder.id,
                    'full_name': record.responder.full_name,
                    'username': record.responder.username,
                    'phone': record.responder.phone,
                    'email': record.responder.email,
                    'role': record.responder.role,
                }
            })
        except PermissionDenied as e:
            return Response({'success': False, 'error': str(e)}, status=403)
