from django.db import models
from django.conf import settings
import math


class Emergency(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('ACCEPTED', 'Accepted'),
        ('HELP_REACHED', 'Help Reached'),
        ('CLOSED', 'Closed'),
        ('CANCELLED', 'Cancelled'),
    ]

    victim = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='emergencies')
    latitude = models.FloatField()
    longitude = models.FloatField()
    address = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    description = models.TextField(blank=True)
    trigger_type = models.CharField(max_length=20, default='button', choices=[('button', 'Button'), ('voice', 'Voice'), ('shake', 'Shake')])
    assigned_guardian = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_emergencies')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    notified_contacts = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='notified_emergencies', blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Emergency #{self.id} - {self.victim.username} ({self.status})"

    def get_nearby_guardians(self, radius_km=3):
        """Find verified, available guardians within radius_km of emergency location."""
        from guardians.models import Guardian
        all_guardians = Guardian.objects.filter(is_verified=True, is_available=True).exclude(
            user=self.victim
        ).select_related('user')
        
        nearby = []
        for guardian in all_guardians:
            if guardian.latitude and guardian.longitude:
                dist = self._haversine_distance(
                    self.latitude, self.longitude,
                    float(guardian.latitude), float(guardian.longitude)
                )
                if dist <= radius_km:
                    guardian.distance_km = dist
                    nearby.append(guardian)
        
        # Sort by distance, then trust score
        nearby.sort(key=lambda g: (g.distance_km, -g.trust_score))
        return nearby

    @staticmethod
    def _haversine_distance(lat1, lon1, lat2, lon2):
        """Calculate distance between two coordinates in km."""
        R = 6371
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = math.sin(d_lat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

    def duration_minutes(self):
        if self.closed_at:
            delta = self.closed_at - self.created_at
            return round(delta.total_seconds() / 60, 1)
        return None
