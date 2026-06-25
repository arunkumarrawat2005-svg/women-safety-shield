from django.utils import timezone
from .models import Emergency
from notifications.services import NotificationService


class EmergencyService:

    @staticmethod
    def create_emergency(user, latitude, longitude, trigger_type='button', description=''):
        """Create emergency and trigger all alerts."""
        emergency = Emergency.objects.create(
            victim=user,
            latitude=latitude,
            longitude=longitude,
            trigger_type=trigger_type,
            description=description,
            status='ACTIVE'
        )

        # Create initial incident event
        EmergencyService._create_event(emergency, 'SOS_CREATED', latitude, longitude)

        # Notify trusted contacts
        EmergencyService._notify_trusted_contacts(emergency)

        # Alert nearby guardians (3km radius)
        EmergencyService._alert_nearby_guardians(emergency)

        return emergency

    @staticmethod
    def _notify_trusted_contacts(emergency):
        from community.models import TrustedContact
        contacts = TrustedContact.objects.filter(user=emergency.victim).select_related('contact')
        for tc in contacts:
            emergency.notified_contacts.add(tc.contact)
            NotificationService.send_sos_alert_to_contact(tc.contact, emergency)

    @staticmethod
    def _alert_nearby_guardians(emergency):
        nearby_guardians = emergency.get_nearby_guardians(radius_km=3)
        for guardian in nearby_guardians:
            NotificationService.send_sos_alert_to_guardian(guardian.user, emergency)
            EmergencyService._create_event(emergency, 'GUARDIAN_NOTIFIED',
                                           emergency.latitude, emergency.longitude)

    @staticmethod
    def accept_emergency(emergency, guardian_user):
        emergency.status = 'ACCEPTED'
        emergency.assigned_guardian = guardian_user
        emergency.save()
        EmergencyService._create_event(emergency, 'GUARDIAN_ACCEPTED',
                                       emergency.latitude, emergency.longitude)
        return emergency

    @staticmethod
    def close_emergency(emergency):
        emergency.status = 'CLOSED'
        emergency.closed_at = timezone.now()
        emergency.save()
        EmergencyService._create_event(emergency, 'EMERGENCY_CLOSED',
                                       emergency.latitude, emergency.longitude)
        return emergency

    @staticmethod
    def _create_event(emergency, event_name, latitude, longitude):
        from incident.models import IncidentEvent
        IncidentEvent.objects.create(
            emergency=emergency,
            event_name=event_name,
            latitude=latitude,
            longitude=longitude
        )
