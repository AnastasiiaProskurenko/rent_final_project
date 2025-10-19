from rest_framework import serializers
from .models import Review, OwnerRating, ListingRating
from apps.users.serializers import UserSerializer
from ..bookings.models import Booking
from django.utils import timezone


class ReviewSerializer(serializers.ModelSerializer):
    booking_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Review
        fields = '__all__'
        read_only_fields = ['booking', 'created_at', 'updated_at']

    def validate_booking_id(self, value):
        try:
            booking = Booking.objects.get(id=value)
        except Booking.DoesNotExist:
            raise serializers.ValidationError("Booking not found.")


        if timezone.now().date() < booking.check_out:
            raise serializers.ValidationError(
                f'You cannot leave a review before your stay ends on {booking.check_out}.'
            )


        if hasattr(booking, 'review'):
            raise serializers.ValidationError("Review already exists for this booking.")


        request = self.context.get('request')
        if request and booking.customer != request.user:
            raise serializers.ValidationError("You can only review your own bookings.")

        return value

    def create(self, validated_data):
        booking_id = validated_data.pop('booking_id')
        booking = Booking.objects.get(id=booking_id)
        return Review.objects.create(booking=booking, **validated_data)



class ListingRatingSerializer(serializers.ModelSerializer):
    rater = UserSerializer(read_only=True)
    listing_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = ListingRating
        fields = '__all__'
        read_only_fields = ('listing', 'rater', 'created_at', 'updated_at')



class OwnerRatingSerializer(serializers.ModelSerializer):
    rater = UserSerializer(read_only=True)
    owner = UserSerializer(read_only=True)
    owner_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = OwnerRating
        fields = '__all__'
        read_only_fields = ('owner', 'rater', 'created_at', 'updated_at')