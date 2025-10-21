from django.db import models
from django.core.validators import MinValueValidator
from apps.common.models import TimeModel
from apps.common.enums import PaymentMethod, PaymentStatus
from django.contrib.auth import get_user_model

User = get_user_model()

class Payment(TimeModel):

    booking = models.OneToOneField('bookings.Booking', on_delete=models.CASCADE, related_name='payment')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    status = models.CharField(max_length=20, choices=PaymentStatus.choices, default='pending')
    
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    payment_details = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['method']),
        ]
    
    def __str__(self):
        return f'Payment {self.id} - {self.amount}€ ({self.status})'

class Refund(TimeModel):

    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='refunds')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=PaymentStatus.choices, default='pending')
    
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_refunds')
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']

    def clean(self):
        super().clean()

        from django.core.exceptions import ValidationError

        if self.payment and self.amount:
            if self.amount > self.payment.amount:
                raise ValidationError(
                    {'amount': f'Refund can not to be more than payment amount.'}
                )
    
    def __str__(self):
        return f'Refund {self.id} - {self.amount}€ ({self.status})'