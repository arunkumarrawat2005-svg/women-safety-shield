from django.contrib import admin
from .models import TrustedContact, SafetyAlert

@admin.register(TrustedContact)
class TrustedContactAdmin(admin.ModelAdmin):
    list_display = ('user', 'contact', 'relation', 'added_at', 'is_active')
    list_filter = ('relation', 'is_active')

@admin.register(SafetyAlert)
class SafetyAlertAdmin(admin.ModelAdmin):
    list_display = ('sender', 'created_at', 'is_broadcast')
