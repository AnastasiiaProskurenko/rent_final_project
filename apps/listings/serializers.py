from rest_framework import serializers
from .models import Listing, ListingPhoto

class ListingPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListingPhoto
        fields = ('id', 'image')

class ListingSerializer(serializers.ModelSerializer):

    photos = ListingPhotoSerializer(many=True, read_only=True)

    class Meta:
        model = Listing

        fields = '__all__'
        read_only_fields = ('owner', 'created_at', 'updated_at')