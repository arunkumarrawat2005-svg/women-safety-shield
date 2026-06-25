from rest_framework import serializers
from .models import Location


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ('id', 'user', 'latitude', 'longitude', 'accuracy', 'speed', 'heading', 'timestamp', 'emergency')
        read_only_fields = ('id', 'user', 'timestamp')
