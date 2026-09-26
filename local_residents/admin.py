from django.contrib import admin
from django.utils import timezone
from .models import LocalResident, LocalResidentResponse


@admin.register(LocalResident)
class LocalResidentAdmin(admin.ModelAdmin):
    list_display = ('user', 'local_resident_type', 'is_verified', 'is_available', 'trust_score', 'total_responses')
    list_filter = ('is_verified', 'is_available', 'local_resident_type')
    search_fields = ('user__username', 'user__email', 'organization_name')
    actions = ['verify_residents']

    def verify_residents(self, request, queryset):
        queryset.update(is_verified=True, verified_at=timezone.now(), verified_by=request.user)
        self.message_user(request, f'{queryset.count()} local residents verified.')
    verify_residents.short_description = 'Verify selected local residents'


@admin.register(LocalResidentResponse)
class LocalResidentResponseAdmin(admin.ModelAdmin):
    list_display = ('sos_event', 'resident', 'status', 'notified_at', 'acknowledged_at')
    list_filter = ('status', 'notified_at')
    search_fields = ('resident__user__username', 'sos_event__id')
