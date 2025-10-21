from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import time
from django.db.models import Q, F

from apps.common.models import TimeModel
from apps.common.enums import BookingStatus
from django.contrib.auth import get_user_model

User = get_user_model()

class Booking(TimeModel):
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='customer_bookings', verbose_name='customer')
    listing = models.ForeignKey('listings.Listing', on_delete=models.CASCADE, related_name='bookings', verbose_name='listing')

    check_in = models.DateField()
    check_out = models.DateField()
    check_in_time = models.TimeField(default=time(15, 0))
    check_out_time = models.TimeField(default=time(12, 0))
    num_guests = models.PositiveIntegerField(default=1, validators= [MinValueValidator(1) ])
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators= [MinValueValidator(0) ])

    status = models.CharField(max_length=20, choices=BookingStatus.choices, default=BookingStatus.WAITING)

    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings_created')

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(check=Q(check_in__lt=F('check_out')), name='check_in_before_check_out'),
        ]

    def clean_check_in(self):

        if self.check_in and self.check_in < timezone.now().date():
            raise ValidationError(
                {'check_in': 'Check-in date cannot be in the past.'}
            )
        return self.check_in

    def clean_check_out(self):

        if self.check_out and self.check_out < timezone.now().date():
            raise ValidationError(
                {'check_out': 'The departure date cannot be in the past.'}
            )
        return self.check_out

    def clean_num_guests(self):

        if self.listing and self.num_guests > self.listing.max_guests:
            raise ValidationError(
                {
                    'num_guests': f'The number of guests ({self.num_guests}) exceeds the maximum for this listing ({self.listing.max_guests})'
                }
            )
        return self.num_guests

    def _validate_booking_overlap(self):
        if not self.listing or not self.check_in or not self.check_out:
            return

        overlapping_bookings = Booking.objects.filter(listing=self.listing,
                                                      status__in=[BookingStatus.WAITING, BookingStatus.AGREED]
                                                      ).filter(check_in__lt=self.check_out, check_out__gt=self.check_in)

        if self.pk:
            overlapping_bookings = overlapping_bookings.exclude(pk=self.pk)

        if overlapping_bookings.exists():
            conflicting = overlapping_bookings.first()
            raise ValidationError(
                f'These dates overlap with an existing booking. '
                f'(from {conflicting.check_in} to {conflicting.check_out})'
            )

    def clean(self):

        super().clean()

        self.clean_check_in()
        self.clean_check_out()
        self.clean_num_guests()

        if not self.check_in or not self.check_out:
            raise ValidationError('Check-in and check-out dates are required.')

        if self.check_out <= self.check_in:
            raise ValidationError(
                {'check_out': 'The departure date must be later than the arrival date.'}
            )
        self._validate_booking_overlap()




    def save(self, *args, **kwargs):

        self.full_clean()

        if self.listing and self.check_in and self.check_out:
            num_days = (self.check_out - self.check_in).days

            self.total_price = self.listing.price * num_days

        super().save(*args, **kwargs)

    def __str__(self):
        return f'Booking #{self.id} by {self.customer.get_full_name()} for {self.listing.title}'