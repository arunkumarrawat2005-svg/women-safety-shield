from django.db import models
from django.conf import settings

class Notification(models.Model):
    NOTIF_TYPES = [('sos','SOS Alert'),('guardian_nearby','Guardian Nearby'),('emergency_update','Emergency Update'),('safety_alert','Safety Alert'),('system','System')]
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notif_type = models.CharField(max_length=30, choices=NOTIF_TYPES, default='system')
    is_read = models.BooleanField(default=False)
    data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ['-created_at']
    def __str__(self): return f"{self.notif_type}: {self.title}"
