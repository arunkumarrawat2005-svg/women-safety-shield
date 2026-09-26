from rest_framework import serializers
from .models import LocalResident, LocalResidentResponse


class LocalResidentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    full_name = serializers.CharField(source='user.full_name', read_only=True)
    phone = serializers.CharField(source='user.phone', read_only=True)
    distance_km = serializers.FloatField(read_only=True, required=False)

    class Meta:
        model = LocalResident
        fields = (
            'id', 'user', 'username', 'full_name', 'phone', 'local_resident_type',
            'is_verified', 'is_available', 'trust_score', 'latitude', 'longitude',
            'organization_name', 'description', 'total_responses', 'successful_responses',
            'distance_km', 'created_at'
        )
        read_only_fields = ('id', 'user', 'is_verified', 'trust_score', 'total_responses', 'successful_responses', 'created_at')


GuardianSerializer = LocalResidentSerializer


class LocalResidentResponseSerializer(serializers.ModelSerializer):
    resident_name = serializers.CharField(source='resident.user.full_name', read_only=True)

    class Meta:
        model = LocalResidentResponse
        fields = ('id', 'sos_event', 'resident', 'resident_name', 'notified_at', 'acknowledged_at', 'status')
        read_only_fields = ('id', 'notified_at')
