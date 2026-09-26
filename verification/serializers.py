from rest_framework import serializers
from .models import VerificationRequest


class VerificationRequestSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    reviewer_name = serializers.CharField(source='reviewed_by.full_name', read_only=True, default='')

    class Meta:
        model = VerificationRequest
        fields = ('id', 'user', 'username', 'aadhaar_document_ref', 'additional_documents', 'reviewed_by', 'reviewer_name', 'status', 'notes', 'reviewed_at', 'created_at')
        read_only_fields = ('id', 'user', 'reviewed_by', 'reviewed_at', 'created_at')
