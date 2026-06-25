from django.db import models
from django.conf import settings


class Guardian(models.Model):
    GUARDIAN_TYPE_CHOICES = [
        ('volunteer', 'Volunteer'),
        ('security', 'Security Staff'),
        ('ngo', 'NGO Member'),
        ('citizen', 'Verified Citizen'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='guardian_profile')
    guardian_type = models.CharField(max_length=20, choices=GUARDIAN_TYPE_CHOICES, default='volunteer')
    is_verified = models.BooleanField(default=False)
    is_available = models.BooleanField(default=False)
    trust_score = models.FloatField(default=5.0)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    verification_document = models.FileField(upload_to='guardian_docs/', null=True, blank=True)
    organization_name = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    total_responses = models.IntegerField(default=0)
    successful_responses = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_guardians')

    class Meta:
        ordering = ['-trust_score']

    def __str__(self):
        return f"Guardian: {self.user.username} ({'Verified' if self.is_verified else 'Pending'})"

    def response_rate(self):
        if self.total_responses == 0:
            return 0
        return round((self.successful_responses / self.total_responses) * 100, 1)

    def update_trust_score(self):
        rate = self.response_rate()
        self.trust_score = min(10.0, (rate / 10) + self.successful_responses * 0.1)
        self.save()
