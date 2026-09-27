from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('user', 'Normal User'),
        ('local_resident', 'Local Resident'),
        ('organization', 'Organization'),
        ('police', 'Police / Law Enforcement'),
        ('admin', 'Admin'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    phone = models.CharField(max_length=15, blank=True)
    profile_pic = models.ImageField(upload_to='profiles/', blank=True, null=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    emergency_contact = models.CharField(max_length=15, blank=True)
    fcm_token = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)
    date_of_birth = models.DateField(null=True, blank=True)
    bio = models.TextField(blank=True)
    location_data_consent = models.BooleanField(default=False, help_text="Opt-in consent for anonymous location data in route safety AI")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.username} ({self.role})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username

    def is_local_resident(self):
        return self.role in ('local_resident', 'guardian')

    def is_guardian(self):
        # Backwards compatibility alias
        return self.is_local_resident()

    def is_organization(self):
        return self.role == 'organization'

    def is_police(self):
        return self.role == 'police' or self.is_staff or self.is_superuser

    @property
    def badge_identity_verified(self):
        if self.is_verified:
            return True
        try:
            if hasattr(self, 'local_resident_profile') and self.local_resident_profile.is_verified:
                return True
        except Exception:
            pass
        return self.verification_requests.filter(status='approved').exists()

    @property
    def badge_community_verified(self):
        return bool(self.badge_identity_verified and (self.is_local_resident() or self.role in ('local_resident', 'organization')))

    @property
    def badge_secure_account(self):
        return bool(self.email and self.phone and self.is_active)

    @property
    def badge_trusted_contact(self):
        try:
            return self.trusted_contacts.exists() or bool(self.emergency_contact)
        except Exception:
            return bool(self.emergency_contact)
    @property
    def is_basic_user(self):
        """Basic User: Immediately granted upon registration. Can seek help, but cannot act as a community helper."""
        return not self.badge_identity_verified and not self.is_staff and not self.is_superuser

    @property
    def can_seek_help(self):
        """Key principle: Anyone can seek help (SOS, Safe Routes, Maps, Safe Journey)."""
        return True

    @property
    def can_act_as_helper(self):
        """Verified users, local residents, or organizations can provide community assistance."""
        if self.is_staff or self.is_superuser:
            return True
        if self.is_local_resident() or self.role in ('local_resident', 'organization', 'guardian'):
            return True
        return bool(self.badge_identity_verified)

    @property
    def can_respond_to_sos(self):
        """Only verified helpers or organizations can accept/respond to another citizen's SOS."""
        return self.can_act_as_helper

    @property
    def can_join_guardian_network(self):
        """Only verified users can participate actively in the guardian responder pool."""
        return bool(self.badge_identity_verified and (self.is_local_resident() or self.role == 'local_resident'))

    @property
    def access_level_display(self):
        """Human-readable access level for UI badges and permission screens."""
        if self.is_staff or self.is_superuser:
            return "Administrator (Full System Oversight)"
        if self.role == 'police':
            return "Law Enforcement / Police (Operational)"
        if self.badge_identity_verified:
            if self.is_local_resident():
                return "Verified Community Guardian / Helper"
            elif self.role == 'organization':
                return "Verified Organization Member"
            return "Verified Citizen (Eligible Helper)"
        return "Basic User (Emergency Seeker Only)"
