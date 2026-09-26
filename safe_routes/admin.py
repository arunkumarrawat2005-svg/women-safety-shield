from django.contrib import admin
from .models import RouteSegment

@admin.register(RouteSegment)
class RouteSegmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'start_lat', 'start_lng', 'end_lat', 'end_lng', 'safety_score', 'last_scored_at')
