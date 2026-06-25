from django.contrib import admin
from .models import SafetyZone, SafetyReport

@admin.register(SafetyZone)
class SafetyZoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'risk_score', 'incident_count', 'latitude', 'longitude')
    list_filter = ('status',)

@admin.register(SafetyReport)
class SafetyReportAdmin(admin.ModelAdmin):
    list_display = ('category', 'location_name', 'user', 'created_at', 'is_verified')
    list_filter = ('category', 'is_verified')
    actions = ['verify_reports']

    def verify_reports(self, request, queryset):
        queryset.update(is_verified=True)
    verify_reports.short_description = 'Verify selected reports'
