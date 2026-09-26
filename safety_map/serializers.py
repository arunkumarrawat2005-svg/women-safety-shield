from rest_framework import serializers
from .models import SafetyZone, SafetyReport


class SafetyZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = SafetyZone
        fields = ('id', 'name', 'latitude', 'longitude', 'radius_meters', 'risk_score', 'status', 'incident_count', 'updated_at')


class SafetyReportSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = SafetyReport
        fields = ('id', 'user', 'user_name', 'latitude', 'longitude', 'location_name', 'category', 'description', 'is_anonymous', 'created_at')
        read_only_fields = ('id', 'user', 'user_name', 'created_at')

    def get_user_name(self, obj):
        if obj.is_anonymous:
            return "Anonymous"
        return obj.user.full_name if obj.user else "Anonymous"

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Bug fix for Doc 12: actually conceal identity when is_anonymous is True
        if instance.is_anonymous:
            data['user'] = None
        return data
