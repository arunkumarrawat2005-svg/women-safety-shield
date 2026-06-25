from django.db import models
from django.conf import settings


class TrustedContact(models.Model):
    RELATION_CHOICES = [
        ('family', 'Family'),
        ('friend', 'Friend'),
        ('colleague', 'Colleague'),
        ('neighbor', 'Neighbor'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='trusted_contacts')
    contact = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='trusted_by')
    relation = models.CharField(max_length=20, choices=RELATION_CHOICES, default='other')
    added_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('user', 'contact')
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.user.username} → {self.contact.username} ({self.relation})"


class SafetyAlert(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_alerts')
    message = models.TextField()
    recipients = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='received_alerts')
    created_at = models.DateTimeField(auto_now_add=True)
    is_broadcast = models.BooleanField(default=False)

    def __str__(self):
        return f"Alert from {self.sender.username} at {self.created_at}"
