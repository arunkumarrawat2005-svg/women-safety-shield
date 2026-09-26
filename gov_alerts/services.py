from django.utils import timezone
from .models import GovAlert


class GovAlertService:
    @staticmethod
    def trigger_emergency_alert(emergency, channel='112_ERSS'):
        """Always fires in parallel with community networks."""
        from incident.models import IncidentEvent

        alert = GovAlert.objects.create(
            sos_event=emergency,
            channel=channel,
            delivery_status='DISPATCHED',
            response_payload={
                'lat': emergency.latitude,
                'lng': emergency.longitude,
                'victim': emergency.victim.username,
                'phone': emergency.victim.phone,
                'dispatched_at': timezone.now().isoformat(),
            }
        )

        # Log incident event
        IncidentEvent.objects.create(
            emergency=emergency,
            event_name='GOV_ALERT_DISPATCHED',
            description=f'Official emergency alert dispatched via {channel}',
            latitude=emergency.latitude,
            longitude=emergency.longitude
        )

        return alert
