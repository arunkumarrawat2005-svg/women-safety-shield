import os
import logging
import requests
from django.conf import settings
from .models import Notification

logger = logging.getLogger(__name__)


def send_fcm_push(fcm_token, title, body, data=None):
    """Send real push notification via FCM."""
    if not fcm_token or not getattr(settings, 'FCM_SERVER_KEY', None):
        return

    payload = {
        "to": fcm_token,
        "notification": {"title": title, "body": body},
        "data": {k: str(v) for k, v in (data or {}).items()}
    }
    headers = {
        "Authorization": f"key={settings.FCM_SERVER_KEY}",
        "Content-Type": "application/json"
    }
    try:
        requests.post("https://fcm.googleapis.com/fcm/send", headers=headers, json=payload, timeout=5)
    except Exception as e:
        logger.error(f"FCM Push error: {e}")


def trigger_twilio_call_or_sms(phone_number, message_text):
    """Twilio voice call / SMS escalation for unacknowledged alerts."""
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    twilio_num = os.getenv('TWILIO_PHONE_NUMBER')

    if not (account_sid and auth_token and twilio_num and phone_number):
        safe_msg = message_text.encode('ascii', errors='replace').decode('ascii')
        logger.info(f"[Simulation] Twilio escalation to {phone_number}: {safe_msg}")
        return False

    try:
        from twilio.rest import Client
        client = Client(account_sid, auth_token)
        # Send SMS first or voice call
        msg = client.messages.create(
            body=message_text,
            from_=twilio_num,
            to=phone_number
        )
        logger.info(f"Twilio message sent: {msg.sid}")
        return True
    except Exception as e:
        logger.error(f"Twilio error: {e}")
        return False


class NotificationService:
    @staticmethod
    def send_sos_alert_to_contact(contact, emergency):
        Notification.objects.create(
            recipient=contact,
            title='🆘 SOS ALERT',
            message=f'{emergency.victim.full_name} has triggered SOS! Location: ({emergency.latitude:.4f}, {emergency.longitude:.4f})',
            notif_type='sos',
            data={'emergency_id': emergency.id, 'lat': emergency.latitude, 'lng': emergency.longitude}
        )
        send_fcm_push(
            fcm_token=getattr(contact, 'fcm_token', None),
            title='🆘 SOS ALERT',
            body=f'{emergency.victim.full_name} needs help! Tap to respond.',
            data={'emergency_id': emergency.id, 'lat': emergency.latitude, 'lng': emergency.longitude}
        )

    @staticmethod
    def send_sos_alert_to_resident(resident_user, emergency, resident=None):
        dist_km = getattr(resident, 'distance_km', None) or getattr(resident_user, '_temp_dist_km', None)
        dist_str = f" (~{dist_km*1000:.0f}m away)" if dist_km else ""
        victim_name = emergency.victim.full_name or emergency.victim.username

        Notification.objects.create(
            recipient=resident_user,
            title='🆘 Emergency Nearby - Local Resident Alert',
            message=f'A woman ({victim_name}) needs help near you{dist_str}! Emergency #{emergency.id}. Please respond immediately.',
            notif_type='sos',
            data={'emergency_id': emergency.id, 'lat': emergency.latitude, 'lng': emergency.longitude}
        )
        send_fcm_push(
            fcm_token=getattr(resident_user, 'fcm_token', None),
            title='🆘 Emergency Nearby!',
            body=f'{victim_name} needs urgent help near you{dist_str}! Emergency #{emergency.id}. Tap to respond.',
            data={'emergency_id': emergency.id, 'lat': emergency.latitude, 'lng': emergency.longitude}
        )
        
        # Immediate SMS escalation to local citizen responder
        phone = getattr(resident_user, 'phone', None)
        if phone:
            sms_body = (
                f"🚨 CITIZEN RESCUE ALERT! {victim_name} needs urgent emergency assistance near you{dist_str}. "
                f"Emergency #{emergency.id}. Location: ({emergency.latitude:.4f}, {emergency.longitude:.4f}). "
                f"Respond & track: /emergency/{emergency.id}/track/"
            )
            trigger_twilio_call_or_sms(phone, sms_body)

    # Backwards compatibility alias
    send_sos_alert_to_guardian = send_sos_alert_to_resident

    @staticmethod
    def send_sos_alert_to_org_volunteer(volunteer_user, org, emergency):
        Notification.objects.create(
            recipient=volunteer_user,
            title=f'🆘 Organization Emergency Alert - {org.name}',
            message=f'Emergency #{emergency.id} requires designated responder assistance near {org.name}.',
            notif_type='sos',
            data={'emergency_id': emergency.id, 'org_id': org.id, 'lat': emergency.latitude, 'lng': emergency.longitude}
        )
        send_fcm_push(
            fcm_token=getattr(volunteer_user, 'fcm_token', None),
            title=f'🆘 SOS Alert ({org.name})',
            body=f'Emergency #{emergency.id} requires immediate response.',
            data={'emergency_id': emergency.id, 'org_id': org.id, 'lat': emergency.latitude, 'lng': emergency.longitude}
        )

    @staticmethod
    def escalate_to_call(user, emergency):
        """Escalates via Twilio voice/SMS if alert remains unacknowledged."""
        if user.phone:
            trigger_twilio_call_or_sms(
                user.phone,
                f"URGENT: Emergency #{emergency.id} near your location requires immediate response. Open Women Safety Shield app to accept."
            )

    @staticmethod
    def send_emergency_update(user, emergency, message):
        Notification.objects.create(
            recipient=user,
            title='Emergency Update',
            message=message,
            notif_type='emergency_update',
            data={'emergency_id': emergency.id}
        )
        send_fcm_push(
            fcm_token=getattr(user, 'fcm_token', None),
            title='Emergency Update',
            body=message,
            data={'emergency_id': emergency.id}
        )

    @staticmethod
    def get_unread_count(user):
        return Notification.objects.filter(recipient=user, is_read=False).count()
