from django.contrib import admin
from .models import Emergency

@admin.register(Emergency)
class EmergencyAdmin(admin.ModelAdmin):
    list_display = ('id', 'victim', 'status', 'trigger_type', 'latitude', 'longitude', 'created_at')
    list_filter = ('status', 'trigger_type')
    search_fields = ('victim__username', 'victim__email')
    readonly_fields = ('created_at', 'updated_at')
