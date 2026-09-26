from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError


class IncidentRecord(models.Model):
    NETWORK_CHOICES = [
        ('local_resident', 'Local Resident Network'),
        ('organization', 'Organization Network'),
    ]
    STATUS_CHOICES = [
        ('dispatched', 'Dispatched'),
        ('en_route', 'En Route'),
        ('arrived', 'Arrived at Scene'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    sos = models.ForeignKey(
        'emergency.Emergency',
        on_delete=models.CASCADE,
        related_name='dispatch_records'
    )
    responder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='incident_dispatch_records'
    )
    network_source = models.CharField(
        max_length=30,
        choices=NETWORK_CHOICES,
        default='local_resident'
    )
    acknowledged_at = models.DateTimeField(default=timezone.now, editable=False)
    arrival_at = models.DateTimeField(null=True, blank=True, editable=False)
    is_arrival_detected = models.BooleanField(default=False)
    masked_responder_id = models.CharField(max_length=60, blank=True)
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='dispatched'
    )
    police_notified_at = models.DateTimeField(null=True, blank=True)
    police_notification_payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-acknowledged_at']
        permissions = [
            ("can_view_responder_identity", "Can view unmasked responder identity in incident records"),
        ]

    def __str__(self):
        return f"Dispatch #{self.id} for SOS #{self.sos_id} ({self.get_network_source_display()})"

    def clean(self):
        if self.pk:
            orig = IncidentRecord.objects.get(pk=self.pk)
            if orig.acknowledged_at and self.acknowledged_at != orig.acknowledged_at:
                raise ValidationError("acknowledged_at is immutable and cannot be modified.")
            if orig.arrival_at and (self.arrival_at != orig.arrival_at):
                raise ValidationError("arrival_at is immutable once recorded.")

    def save(self, *args, **kwargs):
        if not self.masked_responder_id:
            prefix = "LR" if self.network_source == 'local_resident' else "ORG"
            self.masked_responder_id = f"Verified Responder #{prefix}-{self.responder_id:03d}"
        if self.pk:
            orig = IncidentRecord.objects.filter(pk=self.pk).first()
            if orig:
                if orig.acknowledged_at:
                    self.acknowledged_at = orig.acknowledged_at
                if orig.arrival_at and not self.arrival_at:
                    self.arrival_at = orig.arrival_at
        super().save(*args, **kwargs)

    def get_masked_label(self, distance_km=None, eta_mins=None):
        source_name = "Local Resident" if self.network_source == 'local_resident' else "Organization Volunteer"
        if eta_mins is not None and eta_mins > 0:
            return f"{source_name} — {int(eta_mins)} min away"
        if distance_km is not None:
            if distance_km < 1.0:
                return f"{source_name} — {int(distance_km * 1000)}m away"
            return f"{source_name} — {distance_km:.1f}km away"
        return self.masked_responder_id or f"Verified Responder #{self.id}"

    def get_masked_phone(self):
        return f"+91 1800-744-353 (Ext {self.id:03d})"


class IncidentBreadcrumb(models.Model):
    incident_record = models.ForeignKey(
        IncidentRecord,
        on_delete=models.CASCADE,
        related_name='breadcrumbs'
    )
    latitude = models.FloatField()
    longitude = models.FloatField()
    accuracy = models.FloatField(null=True, blank=True)
    speed = models.FloatField(null=True, blank=True)
    distance_to_victim_meters = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"Breadcrumb #{self.id} for Record #{self.incident_record_id} @ {self.timestamp.strftime('%H:%M:%S')}"

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError("IncidentBreadcrumb points are append-only and cannot be updated once created.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("IncidentBreadcrumb points are permanent records and cannot be deleted.")


class IncidentRecordAuditLog(models.Model):
    incident_record = models.ForeignKey(
        IncidentRecord,
        on_delete=models.CASCADE,
        related_name='audit_logs'
    )
    admin_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='incident_record_audit_logs'
    )
    accessed_at = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    access_reason = models.TextField(
        help_text="Mandatory legal/investigative justification for unmasking responder identity."
    )

    class Meta:
        ordering = ['-accessed_at']

    def __str__(self):
        return f"Audit: Admin {self.admin_user.username} viewed Record #{self.incident_record_id} @ {self.accessed_at}"


class IdentityRevealRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Responder Consent'),
        ('consented', 'Mutual Consent Granted'),
        ('declined', 'Declined by Responder'),
    ]

    incident_record = models.ForeignKey(
        IncidentRecord,
        on_delete=models.CASCADE,
        related_name='reveal_requests'
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_reveal_requests'
    )
    requested_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_reveal_requests'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    requested_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-requested_at']

    def __str__(self):
        return f"Reveal Request #{self.id} for Record #{self.incident_record_id} ({self.status})"
