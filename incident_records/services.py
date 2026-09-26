import math
import logging
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import PermissionDenied
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)

from .models import (
    IncidentRecord,
    IncidentBreadcrumb,
    IncidentRecordAuditLog,
    IdentityRevealRequest
)


class IncidentRecordService:

    @staticmethod
    def _haversine_distance_meters(lat1, lon1, lat2, lon2):
        """Calculate the great-circle distance between two points on Earth in meters."""
        R = 6371000.0  # Earth radius in meters
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = (
            math.sin(delta_phi / 2.0) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return R * c

    @staticmethod
    def create_dispatch_record(emergency, responder_user, network_source='local_resident'):
        """
        Feature 1 & Feature 2:
        Creates a server-side, tamper-proof IncidentRecord when a responder accepts an SOS,
        and automatically executes the parallel Police Handoff.
        """
        with transaction.atomic():
            record, created = IncidentRecord.objects.get_or_create(
                sos=emergency,
                responder=responder_user,
                defaults={
                    'network_source': network_source,
                    'acknowledged_at': timezone.now(),
                    'status': 'dispatched',
                }
            )
            if not created and record.status == 'cancelled':
                record.status = 'dispatched'
                record.save()

            # Execute Feature 2: Automatic Police Handoff
            IncidentRecordService._push_police_handoff(record)

        return record

    @staticmethod
    def _push_police_handoff(record):
        """
        Feature 2: Automatic Police Handoff
        Push verified responder credentials, dispatch timestamp, and emergency details
        to the parallel police channel (GovAlert + Channels 'police_alerts').
        """
        emergency = record.sos
        responder = record.responder

        # Extract verified credentials
        responder_info = {
            'user_id': responder.id,
            'full_name': responder.full_name,
            'username': responder.username,
            'phone': responder.phone,
            'network_source': record.network_source,
            'dispatched_at': record.acknowledged_at.isoformat(),
            'record_id': record.id,
        }

        if record.network_source == 'local_resident':
            from local_residents.models import LocalResident
            resident = LocalResident.objects.filter(user=responder).first()
            if resident:
                responder_info.update({
                    'role_type': resident.get_local_resident_type_display(),
                    'is_verified': resident.is_verified,
                    'trust_score': resident.trust_score,
                    'total_responses': resident.total_responses,
                    'verified_at': resident.verified_at.isoformat() if resident.verified_at else None,
                })
        else:
            from organization.models import OrgVolunteer
            volunteer = OrgVolunteer.objects.filter(user=responder).first()
            if volunteer:
                responder_info.update({
                    'organization_name': volunteer.organization.name,
                    'role_at_org': volunteer.role_at_org,
                    'approved_by_org': volunteer.approved_by_org,
                    'verification_status': volunteer.verification_status,
                })

        payload = {
            'emergency_id': emergency.id,
            'victim': {
                'username': emergency.victim.username,
                'full_name': emergency.victim.full_name,
                'phone': emergency.victim.phone,
            },
            'emergency_location': {
                'latitude': emergency.latitude,
                'longitude': emergency.longitude,
                'address': emergency.address or 'Pinned GPS Location',
            },
            'dispatched_responder': responder_info,
            'timestamp': timezone.now().isoformat(),
            'certificate_notice': (
                f"OFFICIAL PLATFORM DISPATCH: {responder.full_name} is an authorized, verified "
                f"responder dispatched by Women Safety Shield at {record.acknowledged_at.strftime('%Y-%m-%d %H:%M:%S')}."
            )
        }

        # 1. Update or create official GovAlert
        try:
            from gov_alerts.models import GovAlert
            GovAlert.objects.create(
                sos_event=emergency,
                channel='112_ERSS',
                delivery_status='DISPATCHED',
                response_payload=payload
            )
        except Exception as e:
            logger.error(f"[IncidentRecords] GovAlert save exception: {e}")

        # 2. Update record
        record.police_notified_at = timezone.now()
        record.police_notification_payload = payload
        record.save(update_fields=['police_notified_at', 'police_notification_payload'])

        # 3. Broadcast to Channels WebSocket group
        try:
            channel_layer = get_channel_layer()
            if channel_layer:
                event_data = {
                    'type': 'emergency_update',
                    'data': {
                        'type': 'police_dispatch_handoff',
                        'emergency_id': emergency.id,
                        'record_id': record.id,
                        'masked_label': record.get_masked_label(),
                        'acknowledged_at': record.acknowledged_at.isoformat(),
                        'police_payload': payload,
                    }
                }
                async_to_sync(channel_layer.group_send)(
                    f'emergency_{emergency.id}',
                    event_data
                )
                async_to_sync(channel_layer.group_send)(
                    'police_alerts',
                    event_data
                )
        except Exception as e:
            logger.error(f"[IncidentRecords] Channels broadcast error: {e}")

    @staticmethod
    def record_location_breadcrumb(responder_user, latitude, longitude, emergency_id=None, accuracy=None, speed=None):
        """
        Feature 1 & Feature 3:
        Logs an immutable GPS breadcrumb from acceptance to arrival,
        detects proximity to victim (<=50m), infers arrival_at,
        and triggers on-arrival evidence-preservation guidance.
        """
        record_qs = IncidentRecord.objects.filter(
            responder=responder_user,
            status__in=['dispatched', 'en_route', 'arrived']
        )
        if emergency_id:
            record_qs = record_qs.filter(sos_id=emergency_id)

        record = record_qs.order_by('-acknowledged_at').first()
        if not record:
            return None

        # Calculate distance to victim
        dist_meters = IncidentRecordService._haversine_distance_meters(
            latitude, longitude,
            record.sos.latitude, record.sos.longitude
        )

        # Create immutable breadcrumb point
        breadcrumb = IncidentBreadcrumb.objects.create(
            incident_record=record,
            latitude=latitude,
            longitude=longitude,
            accuracy=accuracy,
            speed=speed,
            distance_to_victim_meters=dist_meters,
            timestamp=timezone.now()
        )

        if record.status == 'dispatched':
            record.status = 'en_route'
            record.save(update_fields=['status'])

        # Check proximity arrival trigger: <= 50.0 meters
        arrival_triggered = False
        if dist_meters <= 50.0 and not record.arrival_at:
            record.arrival_at = timezone.now()
            record.is_arrival_detected = True
            record.status = 'arrived'
            record.save(update_fields=['arrival_at', 'is_arrival_detected', 'status'])
            arrival_triggered = True

            # Log incident event
            try:
                from incident.models import IncidentEvent
                IncidentEvent.objects.create(
                    emergency=record.sos,
                    event_name='RESIDENT_ARRIVED',
                    description=f'Platform verified responder reached scene ({dist_meters:.1f}m proximity detected)',
                    latitude=latitude,
                    longitude=longitude,
                    actor=responder_user
                )
            except Exception as e:
                logger.error(f"[IncidentRecords] IncidentEvent log error: {e}")

        # Broadcast live location and on-arrival guidance if triggered
        try:
            channel_layer = get_channel_layer()
            if channel_layer:
                # 1. Update emergency room
                msg = {
                    'type': 'emergency_update',
                    'data': {
                        'type': 'responder_location',
                        'emergency_id': record.sos.id,
                        'record_id': record.id,
                        'latitude': latitude,
                        'longitude': longitude,
                        'distance_meters': round(dist_meters, 1),
                        'masked_label': record.get_masked_label(distance_km=dist_meters/1000.0),
                        'arrived': record.is_arrival_detected,
                        'arrival_at': record.arrival_at.isoformat() if record.arrival_at else None,
                        'show_arrival_guidance': arrival_triggered,
                    }
                }
                async_to_sync(channel_layer.group_send)(
                    f'emergency_{record.sos.id}',
                    msg
                )
                # 2. Update police stream
                police_msg = {
                    'type': 'emergency_update',
                    'data': {
                        'type': 'police_route_update',
                        'emergency_id': record.sos.id,
                        'record_id': record.id,
                        'latitude': latitude,
                        'longitude': longitude,
                        'timestamp': breadcrumb.timestamp.isoformat(),
                        'distance_to_victim_meters': round(dist_meters, 1),
                        'arrived': record.is_arrival_detected,
                    }
                }
                async_to_sync(channel_layer.group_send)(
                    'police_alerts',
                    police_msg
                )
        except Exception as e:
            logger.error(f"[IncidentRecords] Broadcast error: {e}")

        return {
            'record': record,
            'breadcrumb': breadcrumb,
            'distance_meters': dist_meters,
            'arrived': record.is_arrival_detected,
            'arrival_triggered': arrival_triggered,
        }

    @staticmethod
    def get_masked_responder_info(emergency, viewer_user):
        """
        Feature 4: Identity Masking (victim-facing only).
        Masks the responder's real identity from the victim during and after the incident.
        Only unmasks if mutual opt-in consent is granted.
        """
        record = IncidentRecord.objects.filter(sos=emergency).order_by('-acknowledged_at').first()
        if not record:
            return None

        # Check if mutual identity reveal is consented
        is_consented = IdentityRevealRequest.objects.filter(
            incident_record=record,
            status='consented'
        ).exists()

        # If viewer is the responder or superuser, they can see themselves
        if viewer_user == record.responder:
            return {
                'is_masked': False,
                'name': record.responder.full_name,
                'phone': record.responder.phone,
                'label': 'You (Responder)',
                'is_self': True,
                'record': record,
                'reveal_status': 'self',
            }

        # If viewer is the victim:
        if viewer_user == emergency.victim:
            reveal_req = IdentityRevealRequest.objects.filter(
                incident_record=record,
                requested_by=viewer_user
            ).first()

            if is_consented:
                return {
                    'is_masked': False,
                    'name': record.responder.full_name,
                    'phone': record.responder.phone,
                    'label': f"Verified Responder: {record.responder.full_name} (Mutually Consented)",
                    'is_self': False,
                    'record': record,
                    'reveal_status': 'consented',
                }
            else:
                return {
                    'is_masked': True,
                    'name': record.masked_responder_id,
                    'phone': record.get_masked_phone(),
                    'label': record.get_masked_label(),
                    'photo_url': None,
                    'relay_phone': record.get_masked_phone(),
                    'is_self': False,
                    'record': record,
                    'reveal_status': reveal_req.status if reveal_req else 'none',
                    'reveal_request_id': reveal_req.id if reveal_req else None,
                }

        # For any other user (e.g. contact or normal user)
        return {
            'is_masked': True,
            'name': record.masked_responder_id,
            'phone': record.get_masked_phone(),
            'label': record.get_masked_label(),
            'photo_url': None,
            'is_self': False,
            'record': record,
            'reveal_status': 'masked',
        }

    @staticmethod
    def log_admin_identity_access(admin_user, incident_record, reason, ip_address=None, user_agent=''):
        """
        Feature 5: Admin Access Controls.
        Requires `can_view_responder_identity` permission and logs unmasking to IncidentRecordAuditLog.
        """
        if not (admin_user.has_perm('incident_records.can_view_responder_identity') or admin_user.is_superuser):
            raise PermissionDenied("You do not possess the required 'can_view_responder_identity' permission.")

        if not reason or len(reason.strip()) < 5:
            raise ValueError("A valid, detailed justification reason is mandatory to unmask responder identity.")

        audit = IncidentRecordAuditLog.objects.create(
            incident_record=incident_record,
            admin_user=admin_user,
            access_reason=reason.strip(),
            ip_address=ip_address,
            user_agent=user_agent or ''
        )
        return audit

    @staticmethod
    def request_identity_reveal(victim_user, emergency_id, notes=''):
        """
        Feature 4: Victim requests mutual identity reveal post-incident.
        """
        from emergency.models import Emergency
        emergency = Emergency.objects.get(id=emergency_id, victim=victim_user)
        record = IncidentRecord.objects.filter(sos=emergency).order_by('-acknowledged_at').first()
        if not record:
            raise ValueError("No active dispatch record found for this emergency.")

        reveal_req, created = IdentityRevealRequest.objects.get_or_create(
            incident_record=record,
            requested_by=victim_user,
            requested_to=record.responder,
            defaults={
                'status': 'pending',
                'notes': notes,
            }
        )
        return reveal_req

    @staticmethod
    def respond_to_reveal_request(responder_user, request_id, consent=True):
        """
        Feature 4: Responder grants or declines identity reveal request.
        """
        reveal_req = IdentityRevealRequest.objects.get(
            id=request_id,
            requested_to=responder_user
        )
        reveal_req.status = 'consented' if consent else 'declined'
        reveal_req.responded_at = timezone.now()
        reveal_req.save()
        return reveal_req
