from rest_framework import serializers
from .models import SafetyZone, SafetyReport


class SafetyZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = SafetyZone
        fields = ('id', 'name', 'latitude', 'longitude', 'radius_meters', 'risk_score', 'status', 'incident_count', 'updated_at')


class SafetyReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = SafetyReport
        fields = ('id', 'user', 'latitude', 'longitude', 'location_name', 'category', 'description', 'is_anonymous', 'created_at')
        read_only_fields = ('id', 'user', 'created_at')
