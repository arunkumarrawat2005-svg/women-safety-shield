from django.contrib import admin
from .models import GovAlert

@admin.register(GovAlert)
class GovAlertAdmin(admin.ModelAdmin):
    list_display = ('id', 'sos_event', 'channel', 'delivery_status', 'sent_at')
    list_filter = ('channel', 'delivery_status')
