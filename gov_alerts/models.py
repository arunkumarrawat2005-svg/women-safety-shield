from django.db import models


class GovAlert(models.Model):
    CHANNEL_CHOICES = [
        ('112_ERSS', '112 National Emergency (ERSS)'),
        ('twilio_sms', 'Police Control Room SMS'),
        ('twilio_call', 'Police Control Room Automated Call'),
    ]
    STATUS_CHOICES = [
        ('DISPATCHED', 'Dispatched'),
        ('DELIVERED', 'Delivered'),
        ('ACKNOWLEDGED', 'Acknowledged by Control Room'),
        ('FAILED', 'Failed'),
    ]

    sos_event = models.ForeignKey('emergency.Emergency', on_delete=models.CASCADE, related_name='gov_alerts')
    channel = models.CharField(max_length=50, choices=CHANNEL_CHOICES, default='112_ERSS')
    sent_at = models.DateTimeField(auto_now_add=True)
    delivery_status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='DISPATCHED')
    response_payload = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f"Gov Alert #{self.id} for SOS #{self.sos_event_id} ({self.channel}) - {self.delivery_status}"
