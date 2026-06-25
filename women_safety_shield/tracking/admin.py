from django.contrib import admin
from .models import Location

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('user', 'latitude', 'longitude', 'timestamp', 'emergency')
    list_filter = ('timestamp',)
    search_fields = ('user__username',)
