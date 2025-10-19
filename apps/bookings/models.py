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
    num_guests = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    status = models.CharField(max_length=20, choices=BookingStatus.choices, default=BookingStatus.WAITING)

    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings_created')

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(check=Q(check_in__lt=F('check_out')), name='check_in_before_check_out'),
        ]


    def save(self, *args, **kwargs):

        if self.listing and self.check_in and self.check_out:
            from apps.common.validators import (
                validate_booking_dates,
                validate_max_guests_per_room,
                validate_booking_overlap
            )
            validate_booking_dates(self.check_in, self.check_out)
            validate_max_guests_per_room(self.num_guests, self.listing.max_guests)


            if not self.pk:

                validate_booking_overlap(self)
            else:

                old_booking = self.__class__.objects.get(pk=self.pk)
                if (self.check_in != old_booking.check_in or
                    self.check_out != old_booking.check_out):
                    validate_booking_overlap(self)


            num_days = (self.check_out - self.check_in).days
            if num_days < 1:
                num_days = 1
            self.total_price = self.listing.price * num_days

        super().save(*args, **kwargs)

    def __str__(self):
        return f'Booking #{self.id} by {self.customer.get_full_name()} for {self.listing.title}'