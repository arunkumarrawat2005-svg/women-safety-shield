from rest_framework import serializers
from .models import Guardian
from accounts.serializers import UserSerializer


class GuardianSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    response_rate = serializers.SerializerMethodField()
    distance_km = serializers.FloatField(read_only=True, required=False)

    class Meta:
        model = Guardian
        fields = ('id', 'user', 'user_details', 'guardian_type', 'is_verified', 'is_available',
                  'trust_score', 'latitude', 'longitude', 'organization_name', 'description',
                  'total_responses', 'successful_responses', 'response_rate', 'distance_km', 'created_at')
        read_only_fields = ('id', 'is_verified', 'trust_score', 'created_at')

    def get_response_rate(self, obj):
        return obj.response_rate()
