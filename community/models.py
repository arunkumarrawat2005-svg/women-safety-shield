from django.db import models
from django.conf import settings


class TrustedContact(models.Model):
    RELATION_CHOICES = [
        ('family', 'Family'),
        ('parent', 'Parent / Guardian'),
        ('sibling', 'Sister / Brother'),
        ('spouse', 'Spouse / Partner'),
        ('friend', 'Friend'),
        ('colleague', 'Colleague / Coworker'),
        ('neighbor', 'Neighbor'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='trusted_contacts')
    contact = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='trusted_by')
    name = models.CharField(max_length=150, blank=True, help_text="Name if external contact")
    phone = models.CharField(max_length=20, blank=True, help_text="Phone number if external contact")
    email = models.EmailField(blank=True, help_text="Optional email if external contact")
    relation = models.CharField(max_length=20, choices=RELATION_CHOICES, default='other')
    is_primary = models.BooleanField(default=False, help_text="Priority #1 emergency contact")
    alert_sms = models.BooleanField(default=True, help_text="Receive instant SMS on SOS")
    alert_call = models.BooleanField(default=True, help_text="Receive automated voice call on SOS")
    alert_whatsapp = models.BooleanField(default=True, help_text="Enabled for WhatsApp SOS dispatch")
    can_view_location = models.BooleanField(default=True, help_text="Can track live GPS during emergency")
    last_tested_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp of last drill ping")
    added_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-is_primary', '-added_at']

    @property
    def display_name(self):
        if self.name:
            return self.name
        if self.contact:
            return self.contact.full_name or self.contact.username
        return "Trusted Contact"

    @property
    def display_phone(self):
        if self.contact and self.contact.phone:
            return self.contact.phone
        return self.phone or ""

    @property
    def display_email(self):
        if self.contact and self.contact.email:
            return self.contact.email
        return self.email or ""

    @property
    def avatar_initial(self):
        name = self.display_name.strip()
        return name[0].upper() if name else "T"

    def __str__(self):
        target = (self.contact.username if self.contact else self.name) or "Contact"
        return f"{self.user.username} → {target} ({self.relation})"


class SafetyAlert(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_alerts')
    message = models.TextField()
    recipients = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='received_alerts')
    created_at = models.DateTimeField(auto_now_add=True)
    is_broadcast = models.BooleanField(default=False)

    def __str__(self):
        return f"Alert from {self.sender.username} at {self.created_at}"
