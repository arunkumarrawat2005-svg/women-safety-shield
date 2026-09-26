from django.contrib import admin
from .models import IncidentRecord, IncidentBreadcrumb, IncidentRecordAuditLog, IdentityRevealRequest


@admin.register(IncidentRecord)
class IncidentRecordAdmin(admin.ModelAdmin):
    # Mask responder in list display to avoid casual unmasked browsing
    list_display = ('id', 'sos', 'masked_responder_id', 'network_source', 'status', 'acknowledged_at', 'arrival_at', 'is_arrival_detected')
    list_filter = ('network_source', 'status', 'is_arrival_detected')
    search_fields = ('masked_responder_id', 'sos__id')
    readonly_fields = ('acknowledged_at', 'arrival_at', 'created_at', 'updated_at', 'police_notified_at')

    def has_delete_permission(self, request, obj=None):
        return False  # Immutable records cannot be deleted


@admin.register(IncidentBreadcrumb)
class IncidentBreadcrumbAdmin(admin.ModelAdmin):
    list_display = ('id', 'incident_record', 'latitude', 'longitude', 'distance_to_victim_meters', 'timestamp')
    readonly_fields = ('incident_record', 'latitude', 'longitude', 'accuracy', 'speed', 'distance_to_victim_meters', 'timestamp')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(IncidentRecordAuditLog)
class IncidentRecordAuditLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'incident_record', 'admin_user', 'accessed_at', 'ip_address')
    readonly_fields = ('incident_record', 'admin_user', 'accessed_at', 'ip_address', 'user_agent', 'access_reason')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(IdentityRevealRequest)
class IdentityRevealRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'incident_record', 'requested_by', 'requested_to', 'status', 'requested_at', 'responded_at')
    list_filter = ('status',)
