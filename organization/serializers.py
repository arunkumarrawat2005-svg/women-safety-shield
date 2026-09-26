from rest_framework import serializers
from .models import Organization, OrgVolunteer, OrgResponse


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ('id', 'name', 'org_type', 'address', 'contact_email', 'contact_phone', 'is_verified', 'description', 'created_at')
        read_only_fields = ('id', 'is_verified', 'created_at')


class OrgVolunteerSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    full_name = serializers.CharField(source='user.full_name', read_only=True)
    phone = serializers.CharField(source='user.phone', read_only=True)

    class Meta:
        model = OrgVolunteer
        fields = ('id', 'organization', 'user', 'username', 'full_name', 'phone', 'verification_status', 'approved_by_org', 'role_at_org', 'is_available', 'latitude', 'longitude', 'created_at')
        read_only_fields = ('id', 'created_at')


class OrgResponseSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    volunteer_name = serializers.CharField(source='volunteer.user.full_name', read_only=True, default='')

    class Meta:
        model = OrgResponse
        fields = ('id', 'sos_event', 'organization', 'organization_name', 'volunteer', 'volunteer_name', 'notified_at', 'acknowledged_at', 'dashboard_alert_sent_at', 'status')
        read_only_fields = ('id', 'notified_at')
