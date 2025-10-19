from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import time

phone_validator = RegexValidator(
    regex=r'^[0-9\-\+\(\)\s]+$',
    message='The phone can only contain numbers, hyphens, pluses, parentheses and spaces.'
)

def validate_booking_dates(check_in, check_out):
    today = timezone.now().date()
    if check_out <= check_in:
        raise ValidationError('Check-out must be after check-in.')
    if check_in < today:
        raise ValidationError('You cannot book dates in the past.')

def validate_review_after_stay(booking):
    today = timezone.now().date()
    if today < booking.check_out:
        raise ValidationError(f'You cannot leave a review before your stay ends on {booking.check_out}.')

def validate_max_guests_per_room(num_guests, max_guests):
    if num_guests > max_guests:
        raise ValidationError(f'Number of guests ({num_guests}) exceeds maximum allowed ({max_guests}).')

def validate_booking_overlap(booking_instance):

    from apps.bookings.models import Booking
    new_in = booking_instance.check_in
    new_out = booking_instance.check_out
    new_in_time = booking_instance.check_in_time or time(15, 0)
    new_out_time = booking_instance.check_out_time or time(12, 0)

    qs = Booking.objects.filter(
        listing=booking_instance.listing,
        status__in=['waiting', 'agreed']
    )
    if booking_instance.pk:
        qs = qs.exclude(pk=booking_instance.pk)

    for b in qs:
        exist_in = b.check_in
        exist_out = b.check_out
        exist_in_time = b.check_in_time or time(15, 0)
        exist_out_time = b.check_out_time or time(12, 0)

        overlaps = (
            (new_in < exist_out or (new_in == exist_out and new_in_time < exist_out_time)) and
            (new_out > exist_in or (new_out == exist_in and new_out_time > exist_in_time))
        )
        if overlaps:
            raise ValidationError(f'This listing is already booked from {exist_in} {exist_in_time} to {exist_out} {exist_out_time}.')