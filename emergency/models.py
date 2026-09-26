import math
from django.db import models
from django.conf import settings


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
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE', db_index=True)
    description = models.TextField(blank=True)
    trigger_type = models.CharField(max_length=20, default='button', choices=[('button', 'Button'), ('voice', 'Voice'), ('shake', 'Shake')])
    assigned_responder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_emergencies'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    notified_contacts = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='notified_emergencies', blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Emergency #{self.id} - {self.victim.username} ({self.status})"

    # Backwards compatibility property for assigned_guardian
    @property
    def assigned_guardian(self):
        return self.assigned_responder

    @assigned_guardian.setter
    def assigned_guardian(self, val):
        self.assigned_responder = val

    def get_nearby_residents(self, radius_km=3):
        """Find verified, available local residents within radius_km of emergency location with bounding-box pre-filter."""
        from local_residents.models import LocalResident
        bb = (radius_km * 1.2) / 111.0  # Approx degrees
        all_residents = LocalResident.objects.filter(
            is_verified=True, 
            is_available=True,
            latitude__range=(self.latitude - bb, self.latitude + bb),
            longitude__range=(self.longitude - bb, self.longitude + bb)
        ).exclude(
            user=self.victim
        ).select_related('user')

        nearby = []
        for resident in all_residents:
            if resident.latitude and resident.longitude:
                dist = self._haversine_distance(
                    self.latitude, self.longitude,
                    float(resident.latitude), float(resident.longitude)
                )
                if dist <= radius_km:
                    resident.distance_km = dist
                    nearby.append(resident)

        nearby.sort(key=lambda g: (g.distance_km, -g.trust_score))
        return nearby

    # Backwards compatibility alias
    get_nearby_guardians = get_nearby_residents

    def get_nearby_org_volunteers(self, radius_km=3):
        """Find approved, available organization volunteers within radius_km."""
        from organization.models import OrgVolunteer
        all_volunteers = OrgVolunteer.objects.filter(approved_by_org=True, is_available=True).exclude(
            user=self.victim
        ).select_related('user', 'organization')

        nearby = []
        for vol in all_volunteers:
            lat = vol.latitude if vol.latitude is not None else (vol.organization.latitude if vol.organization else None)
            lon = vol.longitude if vol.longitude is not None else (vol.organization.longitude if vol.organization else None)
            if lat is not None and lon is not None:
                dist = self._haversine_distance(
                    self.latitude, self.longitude,
                    float(lat), float(lon)
                )
                if dist <= radius_km:
                    vol.distance_km = dist
                    nearby.append(vol)
        nearby.sort(key=lambda v: v.distance_km)
        return nearby

    @staticmethod
    def _haversine_distance(lat1, lon1, lat2, lon2):
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
