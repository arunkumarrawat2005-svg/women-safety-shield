from django.db import models
from django.conf import settings


class IncidentEvent(models.Model):
    EVENT_CHOICES = [
        ('SOS_CREATED', 'SOS Created'),
        ('GUARDIAN_NOTIFIED', 'Guardian Notified'),
        ('GUARDIAN_ACCEPTED', 'Guardian Accepted'),
        ('GUARDIAN_MOVING', 'Guardian Moving'),
        ('GUARDIAN_ARRIVED', 'Guardian Arrived'),
        ('HELP_PROVIDED', 'Help Provided'),
        ('EMERGENCY_CLOSED', 'Emergency Closed'),
        ('CONTACT_NOTIFIED', 'Trusted Contact Notified'),
        ('LOCATION_UPDATED', 'Location Updated'),
    ]

    emergency = models.ForeignKey('emergency.Emergency', on_delete=models.CASCADE, related_name='events')
    event_name = models.CharField(max_length=50, choices=EVENT_CHOICES)
    description = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.emergency} - {self.event_name} @ {self.timestamp}"


class IncidentReport(models.Model):
    emergency = models.OneToOneField('emergency.Emergency', on_delete=models.CASCADE, related_name='report')
    report_number = models.CharField(max_length=50, unique=True)
    summary = models.TextField()
    response_time_minutes = models.FloatField(null=True, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Report #{self.report_number}"
