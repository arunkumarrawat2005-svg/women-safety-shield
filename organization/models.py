from django.db import models
from django.conf import settings


class Organization(models.Model):
    ORG_TYPE_CHOICES = [
        ('college', 'College'),
        ('company', 'Company'),
        ('hospital', 'Hospital'),
        ('ngo', 'NGO'),
        ('government', 'Government'),
        ('other', 'Other'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='organization')
    name = models.CharField(max_length=200)
    org_type = models.CharField(max_length=20, choices=ORG_TYPE_CHOICES)
    address = models.TextField()
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=15)
    latitude = models.FloatField(null=True, blank=True, help_text="Campus / facility latitude")
    longitude = models.FloatField(null=True, blank=True, help_text="Campus / facility longitude")
    city = models.CharField(max_length=100, blank=True, default='')
    state = models.CharField(max_length=100, blank=True, default='')
    emergency_helpline = models.CharField(max_length=20, blank=True, default='', help_text="24/7 Security Control Room Hotline")
    operating_hours = models.CharField(max_length=100, blank=True, default='24/7 Security Coverage')
    has_safe_haven = models.BooleanField(default=True, help_text="Designated safe haven / shelter for women in distress")
    cctv_monitored = models.BooleanField(default=True, help_text="CCTV monitored perimeter")
    security_guards_count = models.IntegerField(default=5, help_text="Estimated security guard team size")
    is_verified = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def get_badge_class(self):
        mapping = {
            'college': 'bg-primary-subtle text-primary border border-primary-subtle',
            'company': 'bg-info-subtle text-info border border-info-subtle',
            'hospital': 'bg-danger-subtle text-danger border border-danger-subtle',
            'ngo': 'bg-success-subtle text-success border border-success-subtle',
            'government': 'bg-warning-subtle text-warning-emphasis border border-warning-subtle',
        }
        return mapping.get(self.org_type, 'bg-secondary-subtle text-secondary border border-secondary-subtle')

    def get_icon(self):
        mapping = {
            'college': 'bi-mortarboard-fill',
            'company': 'bi-building-check',
            'hospital': 'bi-hospital-fill',
            'ngo': 'bi-heart-pulse-fill',
            'government': 'bi-shield-shaded',
        }
        return mapping.get(self.org_type, 'bi-building')

    @property
    def hotline_display(self):
        return self.emergency_helpline or self.contact_phone


class OrgVolunteer(models.Model):
    VERIFICATION_CHOICES = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='volunteers')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='org_volunteer_profiles')
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_CHOICES, default='pending')
    approved_by_org = models.BooleanField(default=False, help_text="Approved by the organization as a designated responder")
    role_at_org = models.CharField(max_length=100, default='designated_responder', help_text="e.g. security_guard, staff, resident_assistant")
    is_available = models.BooleanField(default=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('organization', 'user')

    def __str__(self):
        return f"{self.user.username} - {self.organization.name} ({self.role_at_org})"


class OrgResponse(models.Model):
    STATUS_CHOICES = [
        ('notified', 'Notified'),
        ('acknowledged', 'Acknowledged'),
        ('declined', 'Declined'),
        ('timed_out', 'Timed Out'),
    ]

    sos_event = models.ForeignKey('emergency.Emergency', on_delete=models.CASCADE, related_name='org_responses')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='sos_responses')
    volunteer = models.ForeignKey(OrgVolunteer, on_delete=models.SET_NULL, null=True, blank=True, related_name='responses')
    notified_at = models.DateTimeField(auto_now_add=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    dashboard_alert_sent_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='notified')

    class Meta:
        ordering = ['-notified_at']

    def __str__(self):
        return f"Org Alert: SOS #{self.sos_event_id} at {self.organization.name} ({self.status})"
