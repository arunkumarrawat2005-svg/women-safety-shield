from rest_framework import serializers
from .models import IncidentEvent, IncidentReport


class IncidentEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncidentEvent
        fields = ('id', 'emergency', 'event_name', 'description', 'timestamp', 'latitude', 'longitude', 'actor')


class IncidentReportSerializer(serializers.ModelSerializer):
    events = IncidentEventSerializer(source='emergency.events', many=True, read_only=True)

    class Meta:
        model = IncidentReport
        fields = ('id', 'emergency', 'report_number', 'summary', 'response_time_minutes', 'generated_at', 'events')
