from .models import Notification

class NotificationService:
    @staticmethod
    def send_sos_alert_to_contact(contact, emergency):
        Notification.objects.create(
            recipient=contact, title='🆘 SOS ALERT',
            message=f'{emergency.victim.full_name} has triggered SOS! Location: ({emergency.latitude:.4f}, {emergency.longitude:.4f})',
            notif_type='sos', data={'emergency_id': emergency.id, 'lat': emergency.latitude, 'lng': emergency.longitude}
        )

    @staticmethod
    def send_sos_alert_to_guardian(guardian_user, emergency):
        Notification.objects.create(
            recipient=guardian_user, title='🆘 Emergency Nearby - Please Help',
            message=f'A woman needs help near you! Emergency #{emergency.id}. Please respond immediately.',
            notif_type='sos', data={'emergency_id': emergency.id, 'lat': emergency.latitude, 'lng': emergency.longitude}
        )

    @staticmethod
    def send_emergency_update(user, emergency, message):
        Notification.objects.create(
            recipient=user, title='Emergency Update', message=message,
            notif_type='emergency_update', data={'emergency_id': emergency.id}
        )

    @staticmethod
    def get_unread_count(user):
        return Notification.objects.filter(recipient=user, is_read=False).count()
