from rest_framework import serializers
from .models import Emergency


class EmergencySerializer(serializers.ModelSerializer):
    victim_name = serializers.CharField(source='victim.full_name', read_only=True)
    responder_name = serializers.CharField(source='assigned_responder.full_name', read_only=True, default='')
    guardian_name = serializers.CharField(source='assigned_responder.full_name', read_only=True, default='')
    duration = serializers.SerializerMethodField()

    class Meta:
        model = Emergency
        fields = (
            'id', 'victim', 'victim_name', 'latitude', 'longitude', 'address',
            'status', 'trigger_type', 'description', 'assigned_responder', 'assigned_guardian',
            'responder_name', 'guardian_name', 'created_at', 'closed_at', 'duration'
        )
        read_only_fields = ('id', 'victim', 'created_at', 'closed_at', 'status')

    def get_duration(self, obj):
        return obj.duration_minutes()


class CreateEmergencySerializer(serializers.Serializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    trigger_type = serializers.ChoiceField(choices=['button', 'voice', 'shake'], default='button')
    description = serializers.CharField(required=False, allow_blank=True)
