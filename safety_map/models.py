from django.db import models
from django.conf import settings


class SafetyZone(models.Model):
    STATUS_CHOICES = [
        ('safe', 'Safe'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
        ('unknown', 'Unknown'),
    ]

    name = models.CharField(max_length=200)
    latitude = models.FloatField()
    longitude = models.FloatField()
    radius_meters = models.IntegerField(default=200)
    risk_score = models.FloatField(default=0.0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unknown')
    incident_count = models.IntegerField(default=0)
    report_count = models.IntegerField(default=0)
    last_incident = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.status})"

    def update_status(self):
        if self.risk_score <= 3.0:
            self.status = 'safe'
        elif self.risk_score <= 6.0:
            self.status = 'medium'
        else:
            self.status = 'high'
        self.save()


class SafetyReport(models.Model):
    CATEGORY_CHOICES = [
        ('harassment', 'Harassment'),
        ('theft', 'Theft/Robbery'),
        ('unsafe_area', 'Unsafe Area'),
        ('poor_lighting', 'Poor Lighting'),
        ('no_crowd', 'Isolated Area'),
        ('accident', 'Accident'),
        ('suspicious', 'Suspicious Activity'),
        ('safe', 'Safe Area'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='safety_reports')
    latitude = models.FloatField()
    longitude = models.FloatField()
    location_name = models.CharField(max_length=200, blank=True)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    is_anonymous = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    upvotes = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.category} at ({self.latitude}, {self.longitude})"
