from django.db import models
from django.conf import settings


class Location(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='locations')
    latitude = models.FloatField()
    longitude = models.FloatField()
    accuracy = models.FloatField(null=True, blank=True)
    speed = models.FloatField(null=True, blank=True)
    heading = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    emergency = models.ForeignKey('emergency.Emergency', on_delete=models.SET_NULL, null=True, blank=True, related_name='locations')

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.username} @ ({self.latitude}, {self.longitude})"
