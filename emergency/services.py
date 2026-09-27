import logging
from django.utils import timezone
from django.db import transaction
from .models import Emergency
from notifications.services import NotificationService

logger = logging.getLogger(__name__)


class EmergencyService:

    @staticmethod
    def create_emergency(user, latitude, longitude, trigger_type='button', description=''):
        """Create emergency and trigger all three channels in parallel."""
        emergency = Emergency.objects.create(
            victim=user,
            latitude=latitude,
            longitude=longitude,
            trigger_type=trigger_type,
            description=description,
            status='ACTIVE'
        )

        # 1. Create initial incident event
        EmergencyService._create_event(emergency, 'SOS_CREATED', latitude, longitude)

        # 2. Notify trusted contacts (community network)
        EmergencyService._notify_trusted_contacts(emergency)

        # 3. Channel 1: Alert nearby Local Residents
        EmergencyService._alert_nearby_residents(emergency)

        # 4. Channel 2: Alert nearby Organization Responders & Dashboard
        EmergencyService._alert_nearby_organizations(emergency)

        # 5. Channel 3: Alert Government / Police in parallel (always fires)
        EmergencyService._alert_government_emergency(emergency)

        return emergency

    @staticmethod
    def _notify_trusted_contacts(emergency):
        from community.models import TrustedContact
        from notifications.services import trigger_twilio_call_or_sms
        contacts = TrustedContact.objects.filter(user=emergency.victim, is_active=True).select_related('contact')
        for tc in contacts:
            if tc.contact:
                emergency.notified_contacts.add(tc.contact)
                NotificationService.send_sos_alert_to_contact(tc.contact, emergency)
            
            phone = tc.display_phone
            if phone and tc.alert_sms:
                victim_name = emergency.victim.full_name or emergency.victim.username
                sms_body = (
                    f"🆘 SOS EMERGENCY! {victim_name} triggered safety alarm. "
                    f"Location: ({emergency.latitude:.4f}, {emergency.longitude:.4f}). "
                    f"Live Tracker: /emergency/{emergency.id}/track/"
                )
                trigger_twilio_call_or_sms(phone, sms_body)

            desc = f"Alert dispatched to trusted contact {tc.name}" + (f" ({phone})" if phone else "")
            EmergencyService._create_event(emergency, 'CONTACT_NOTIFIED', emergency.latitude, emergency.longitude, description=desc, actor=tc.contact)

    @staticmethod
    def _alert_nearby_residents(emergency):
        from local_residents.models import LocalResidentResponse
        nearby_residents = emergency.get_nearby_residents(radius_km=3)
        for resident in nearby_residents:
            # Create per-responder response tracking model (doc 05/09/13)
            LocalResidentResponse.objects.get_or_create(
                sos_event=emergency,
                resident=resident,
                defaults={'status': 'notified'}
            )
            # Deliver notification: In-app, Web Push, and SMS
            NotificationService.send_sos_alert_to_resident(resident.user, emergency, resident=resident)
            
            # Link resident to emergency notified contacts for full audit visibility
            if resident.user:
                try:
                    emergency.notified_contacts.add(resident.user)
                except Exception:
                    pass

            # Create rich timeline entry with distance and badge
            name = resident.user.get_full_name() or resident.user.username
            dist_txt = f"{resident.distance_km*1000:.0f}m away" if resident.distance_km < 1 else f"{resident.distance_km:.1f}km away"
            desc = f"Emergency broadcast dispatched to local citizen {name} ({resident.badge_title}) - ~{dist_txt}"
            EmergencyService._create_event(
                emergency,
                'RESIDENT_NOTIFIED',
                emergency.latitude,
                emergency.longitude,
                description=desc,
                actor=resident.user
            )

    @staticmethod
    def _alert_nearby_organizations(emergency):
        from organization.models import OrgResponse, Organization
        nearby_volunteers = emergency.get_nearby_org_volunteers(radius_km=3)

        notified_orgs = set()
        for vol in nearby_volunteers:
            OrgResponse.objects.get_or_create(
                sos_event=emergency,
                organization=vol.organization,
                defaults={
                    'volunteer': vol,
                    'dashboard_alert_sent_at': timezone.now(),
                    'status': 'notified'
                }
            )
            notified_orgs.add(vol.organization.id)
            NotificationService.send_sos_alert_to_org_volunteer(vol.user, vol.organization, emergency)
            EmergencyService._create_event(emergency, 'ORG_VOLUNTEER_NOTIFIED', emergency.latitude, emergency.longitude)

        # Also alert all registered organizations within region for dashboard awareness
        for org in Organization.objects.filter(is_verified=True).exclude(id__in=notified_orgs)[:5]:
            OrgResponse.objects.get_or_create(
                sos_event=emergency,
                organization=org,
                defaults={
                    'dashboard_alert_sent_at': timezone.now(),
                    'status': 'notified'
                }
            )

    @staticmethod
    def _alert_government_emergency(emergency):
        try:
            from gov_alerts.services import GovAlertService
            GovAlertService.trigger_emergency_alert(emergency, channel='112_ERSS')
        except Exception as e:
            logger.error(f"Gov alert error: {e}")

    @staticmethod
    def accept_emergency(emergency, responder_user):
        """
        Accepts emergency with select_for_update race-condition protection (Doc 18).
        Updates per-responder acknowledgment state in LocalResidentResponse / OrgResponse.
        """
        with transaction.atomic():
            locked_emergency = Emergency.objects.select_for_update().get(pk=emergency.pk)
            locked_emergency.status = 'ACCEPTED'
            locked_emergency.assigned_responder = responder_user
            locked_emergency.save()

            # Check if responder is a LocalResident
            from local_residents.models import LocalResident, LocalResidentResponse
            resident = LocalResident.objects.filter(user=responder_user).first()
            if resident:
                resp, _ = LocalResidentResponse.objects.get_or_create(sos_event=locked_emergency, resident=resident)
                resp.status = 'acknowledged'
                resp.acknowledged_at = timezone.now()
                resp.save()
                EmergencyService._create_event(locked_emergency, 'RESIDENT_ACCEPTED', locked_emergency.latitude, locked_emergency.longitude)

            # Check if responder is an OrgVolunteer
            from organization.models import OrgVolunteer, OrgResponse
            volunteer = OrgVolunteer.objects.filter(user=responder_user).first()
            if volunteer:
                org_resp, _ = OrgResponse.objects.get_or_create(sos_event=locked_emergency, organization=volunteer.organization)
                org_resp.volunteer = volunteer
                org_resp.status = 'acknowledged'
                org_resp.acknowledged_at = timezone.now()
                org_resp.save()
                EmergencyService._create_event(locked_emergency, 'ORG_VOLUNTEER_ACCEPTED', locked_emergency.latitude, locked_emergency.longitude)

            # Feature 1 & 2: Create server-side, tamper-proof IncidentRecord & trigger Police Handoff
            try:
                from incident_records.services import IncidentRecordService
                network_source = 'organization' if volunteer else 'local_resident'
                IncidentRecordService.create_dispatch_record(
                    emergency=locked_emergency,
                    responder_user=responder_user,
                    network_source=network_source
                )
            except Exception as e:
                logger.error(f"[EmergencyService] IncidentRecord creation error: {e}")

        return locked_emergency

    @staticmethod
    def close_emergency(emergency):
        emergency.status = 'CLOSED'
        emergency.closed_at = timezone.now()
        emergency.save()
        EmergencyService._create_event(emergency, 'EMERGENCY_CLOSED', emergency.latitude, emergency.longitude)
        return emergency

    @staticmethod
    def _create_event(emergency, event_name, latitude, longitude, description='', actor=None):
        from incident.models import IncidentEvent
        IncidentEvent.objects.create(
            emergency=emergency,
            event_name=event_name,
            latitude=latitude,
            longitude=longitude,
            description=description,
            actor=actor
        )
