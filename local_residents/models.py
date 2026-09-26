from django.db import models
from django.conf import settings


class LocalResident(models.Model):
    LOCAL_RESIDENT_TYPE_CHOICES = [
        ('volunteer', 'Volunteer'),
        ('security', 'Security Staff'),
        ('ngo', 'NGO Member'),
        ('citizen', 'Verified Citizen'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='local_resident_profile')
    local_resident_type = models.CharField(max_length=20, choices=LOCAL_RESIDENT_TYPE_CHOICES, default='volunteer')
    is_verified = models.BooleanField(default=False)
    is_available = models.BooleanField(default=False)
    trust_score = models.FloatField(default=5.0)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    verification_document = models.FileField(upload_to='resident_docs/', null=True, blank=True)
    organization_name = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100, blank=True, default='Delhi NCR')
    area = models.CharField(max_length=150, blank=True, default='Central Zone')
    skills = models.CharField(max_length=255, blank=True, default='First Aid, Night Watch, Safe Haven Room')
    badge_title = models.CharField(max_length=100, blank=True, default='Community Guardian')
    response_time_min = models.IntegerField(default=3, help_text="Average response time in minutes")
    description = models.TextField(blank=True)
    total_responses = models.IntegerField(default=0)
    successful_responses = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_residents'
    )

    class Meta:
        ordering = ['-trust_score']
        verbose_name = 'Local Resident'
        verbose_name_plural = 'Local Residents'

    def __str__(self):
        status_label = 'Verified' if self.is_verified else 'Pending'
        return f"Local Resident: {self.user.username} ({status_label})"

    @property
    def guardian_type(self):
        return self.local_resident_type

    @guardian_type.setter
    def guardian_type(self, val):
        self.local_resident_type = val

    def get_guardian_type_display(self):
        return self.get_local_resident_type_display()

    def response_rate(self):
        if self.total_responses == 0:
            return 0
        return round((self.successful_responses / self.total_responses) * 100, 1)

    def update_trust_score(self):
        rate = self.response_rate()
        self.trust_score = min(10.0, (rate / 10) + self.successful_responses * 0.1)
        self.save()

    @property
    def radius_km(self):
        return 3

    @property
    def skill_list(self):
        if not self.skills:
            return ['Community Safety', 'First Aid', 'Safe Haven Room']
        if ',' in self.skills:
            return [s.strip() for s in self.skills.split(',') if s.strip()]
        return [s.strip() for s in self.skills.split() if s.strip()]


# Backwards compatibility alias
Guardian = LocalResident


class LocalResidentResponse(models.Model):
    STATUS_CHOICES = [
        ('notified', 'Notified'),
        ('acknowledged', 'Acknowledged'),
        ('declined', 'Declined'),
        ('timed_out', 'Timed Out'),
    ]

    sos_event = models.ForeignKey('emergency.Emergency', on_delete=models.CASCADE, related_name='resident_responses')
    resident = models.ForeignKey(LocalResident, on_delete=models.CASCADE, related_name='responses')
    notified_at = models.DateTimeField(auto_now_add=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='notified')

    class Meta:
        ordering = ['-notified_at']

    def __str__(self):
        return f"Response for SOS #{self.sos_event_id} by {self.resident.user.username} ({self.status})"


class SafeEscortRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='escort_requests')
    resident = models.ForeignKey(LocalResident, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_escorts')
    pickup_location = models.CharField(max_length=255)
    destination = models.CharField(max_length=255)
    scheduled_time = models.CharField(max_length=100, default='Immediate')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Safe Escort Request by {self.requester.username} ({self.status})"

