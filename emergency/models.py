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
        """
        Find nearby local residents, community guardians, and active citizen responders within radius_km.
        Checks LocalResident coordinates, falls back to latest Location breadcrumb,
        and includes registered local residents, guardians, and verified citizens.
        """
        from local_residents.models import LocalResident
        from tracking.models import Location
        from django.db.models import Q
        from accounts.models import User

        # Ensure all registered local residents, guardians, or verified users have a LocalResident profile
        eligible_users = User.objects.filter(
            Q(role__in=['local_resident', 'guardian', 'volunteer', 'citizen']) |
            Q(is_verified=True) |
            Q(local_resident_profile__isnull=False)
        ).exclude(id=self.victim_id).distinct()

        for u in eligible_users:
            res, _ = LocalResident.objects.get_or_create(
                user=u,
                defaults={
                    'local_resident_type': 'citizen' if u.role == 'user' else (u.role if u.role in ['volunteer', 'security', 'ngo', 'citizen'] else 'citizen'),
                    'city': u.city or 'Delhi NCR',
                    'area': u.address or u.city or 'Central Zone',
                    'badge_title': 'Verified Citizen Guardian',
                    'is_verified': True,
                    'is_available': True,
                }
            )
            # Sync coordinates from Location breadcrumbs if missing on profile
            if res.latitude is None or res.longitude is None:
                loc = Location.objects.filter(user=u).order_by('-timestamp').first()
                if loc:
                    res.latitude = loc.latitude
                    res.longitude = loc.longitude
                    res.is_available = True
                    res.save()

        # Query all resident candidates
        candidates = LocalResident.objects.exclude(user=self.victim).select_related('user')
        nearby = []
        for resident in candidates:
            lat = resident.latitude
            lng = resident.longitude
            if lat is None or lng is None:
                loc = Location.objects.filter(user=resident.user).order_by('-timestamp').first()
                if loc:
                    lat = loc.latitude
                    lng = loc.longitude
                    resident.latitude = lat
                    resident.longitude = lng
                    resident.save()

            if lat is not None and lng is not None:
                dist = self._haversine_distance(
                    float(self.latitude), float(self.longitude),
                    float(lat), float(lng)
                )
                if dist <= radius_km:
                    resident.distance_km = dist
                    resident._temp_dist_km = dist
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
