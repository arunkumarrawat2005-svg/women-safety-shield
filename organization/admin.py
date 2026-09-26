from django.contrib import admin
from .models import Organization, OrgVolunteer, OrgResponse


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'org_type', 'user', 'contact_email', 'contact_phone', 'is_verified', 'created_at')
    list_filter = ('org_type', 'is_verified')
    search_fields = ('name', 'contact_email', 'user__username')


@admin.register(OrgVolunteer)
class OrgVolunteerAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization', 'role_at_org', 'approved_by_org', 'is_available', 'verification_status')
    list_filter = ('approved_by_org', 'is_available', 'verification_status', 'organization')
    search_fields = ('user__username', 'organization__name')


@admin.register(OrgResponse)
class OrgResponseAdmin(admin.ModelAdmin):
    list_display = ('sos_event', 'organization', 'volunteer', 'status', 'notified_at', 'acknowledged_at', 'dashboard_alert_sent_at')
    list_filter = ('status', 'organization')
