from rest_framework import serializers
from .models import Branch

class BranchSerializer(serializers.ModelSerializer):
    distance_km = serializers.SerializerMethodField()

    class Meta:
        model = Branch
        fields = [
            'id', 'name', 'slug', 'address', 'latitude', 'longitude',
            'gmaps_url', 'opening_hours', 'is_active', 'distance_km'
        ]

    def get_distance_km(self, obj):
        # Dipasok via serializer context jika ada user_lat & user_lng
        user_lat = self.context.get('user_lat')
        user_lng = self.context.get('user_lng')
        if user_lat is not None and user_lng is not None:
            return obj.distance_to(float(user_lat), float(user_lng))
        return None
