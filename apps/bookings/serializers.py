from rest_framework import serializers
from .models import Booking
from apps.listings.serializers import ListingSerializer
from apps.users.serializers import UserSerializer


class BookingSerializer(serializers.ModelSerializer):
    customer = UserSerializer(read_only=True)
    listing = ListingSerializer(read_only=True)
    customer_id = serializers.IntegerField(write_only=True)
    listing_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Booking
        fields ='__all__'
        read_only_fields = ('total_price', 'created_at', 'updated_at')
    
    def validate(self, data):

        if data['check_in'] >= data['check_out']:
            raise serializers.ValidationError("Check-out must be after check-in.")
        

        listing_id = data.get('listing_id')
        if listing_id:
            from apps.listings.models import Listing
            try:
                listing = Listing.objects.get(id=listing_id)
                if data['num_guests'] > listing.max_guests:
                    raise serializers.ValidationError(
                        f"Number of guests ({data['num_guests']}) exceeds maximum allowed ({listing.max_guests})."
                    )
            except Listing.DoesNotExist:
                raise serializers.ValidationError("Listing not found.")
        
        return data


class BookingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = '__all__'
    
    def create(self, validated_data):
        validated_data['customer'] = self.context['request'].user
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

