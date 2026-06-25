from django.contrib import admin
from .models import IncidentEvent, IncidentReport

@admin.register(IncidentEvent)
class IncidentEventAdmin(admin.ModelAdmin):
    list_display = ('emergency', 'event_name', 'timestamp', 'actor')
    list_filter = ('event_name',)

@admin.register(IncidentReport)
class IncidentReportAdmin(admin.ModelAdmin):
    list_display = ('report_number', 'emergency', 'response_time_minutes', 'generated_at')
