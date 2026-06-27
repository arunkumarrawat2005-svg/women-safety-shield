from rest_framework import serializers
from .models import TrustedContact
from accounts.serializers import UserSerializer


class TrustedContactSerializer(serializers.ModelSerializer):
    contact_details = UserSerializer(source='contact', read_only=True)

    class Meta:
        model = TrustedContact
        fields = ('id', 'user', 'contact', 'contact_details', 'relation', 'added_at', 'is_active')
        read_only_fields = ('id', 'user', 'added_at')
