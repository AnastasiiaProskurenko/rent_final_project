from rest_framework import serializers
from .models import Payment, Refund
from apps.users.serializers import UserSerializer


class PaymentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    booking_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class RefundSerializer(serializers.ModelSerializer):
    payment = PaymentSerializer(read_only=True)
    processed_by = UserSerializer(read_only=True)
    payment_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Refund
        fields = '__all__'
        read_only_fields = ('processed_by', 'processed_at', 'created_at', 'updated_at')

