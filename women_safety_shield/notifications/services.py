from .models import Notification
import requests
import json

def send_fcm_push(fcm_token, title, body, data=None):
    """Send real push notification via FCM."""
    if not fcm_token:
        return
    
    from django.conf import settings
    payload = {
        "message": {
            "token": fcm_token,
            "notification": {
                "title": title,
                "body": body
            },
            "data": {k: str(v) for k, v in (data or {}).items()}
        }
    }
    headers = {
        "Authorization": f"key={settings.FCM_SERVER_KEY}",
        "Content-Type": "application/json"
    }
    requests.post(
        "https://fcm.googleapis.com/fcm/send",
        headers={"Authorization": f"key={settings.FCM_SERVER_KEY}", "Content-Type": "application/json"},
        json={
            "to": fcm_token,
            "notification": {"title": title, "body": body},
            "data": {k: str(v) for k, v in (data or {}).items()}
        }
    )

class NotificationService:
    @staticmethod
    def send_sos_alert_to_contact(contact, emergency):
        Notification.objects.create(
            recipient=contact, title='🆘 SOS ALERT',
            message=f'{emergency.victim.full_name} has triggered SOS! Location: ({emergency.latitude:.4f}, {emergency.longitude:.4f})',
            notif_type='sos', data={'emergency_id': emergency.id, 'lat': emergency.latitude, 'lng': emergency.longitude}
        )
        # Send real push notification
        send_fcm_push(
            fcm_token=getattr(contact, 'fcm_token', None),
            title='🆘 SOS ALERT',
            body=f'{emergency.victim.full_name} needs help! Tap to respond.',
            data={'emergency_id': emergency.id, 'lat': emergency.latitude, 'lng': emergency.longitude}
        )

    @staticmethod
    def send_sos_alert_to_guardian(guardian_user, emergency):
        Notification.objects.create(
            recipient=guardian_user, title='🆘 Emergency Nearby - Please Help',
            message=f'A woman needs help near you! Emergency #{emergency.id}. Please respond immediately.',
            notif_type='sos', data={'emergency_id': emergency.id, 'lat': emergency.latitude, 'lng': emergency.longitude}
        )
        # Send real push notification
        send_fcm_push(
            fcm_token=getattr(guardian_user, 'fcm_token', None),
            title='🆘 Emergency Nearby!',
            body=f'A woman needs help near you! Emergency #{emergency.id}. Please respond immediately.',
            data={'emergency_id': emergency.id, 'lat': emergency.latitude, 'lng': emergency.longitude}
        )

    @staticmethod
    def send_emergency_update(user, emergency, message):
        Notification.objects.create(
            recipient=user, title='Emergency Update', message=message,
            notif_type='emergency_update', data={'emergency_id': emergency.id}
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