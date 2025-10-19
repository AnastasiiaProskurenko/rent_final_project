from rest_framework import serializers
from .models import ListingView


class ListingViewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    listing = serializers.StringRelatedField(read_only=True)
    listing_id = serializers.IntegerField(write_only=True)
    user_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = ListingView
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

