from datetime import date, datetime
from types import SimpleNamespace
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase
from django.utils import timezone

from apps.common.validators import (
    validate_booking_dates,
    validate_max_guests_per_room,
    validate_review_after_stay,
)


class ValidateBookingDatesTests(SimpleTestCase):
    def test_checkout_before_checkin_raises_error(self):
        check_in = date(2024, 1, 10)
        check_out = date(2024, 1, 9)
        frozen_now = timezone.make_aware(datetime(2024, 1, 1))
        with patch('apps.common.validators.timezone.now', return_value=frozen_now):
            with self.assertRaisesMessage(ValidationError, 'Check-out must be after check-in.'):
                validate_booking_dates(check_in, check_out)

    def test_past_checkin_raises_error(self):
        check_in = date(2023, 12, 31)
        check_out = date(2024, 1, 2)
        frozen_now = timezone.make_aware(datetime(2024, 1, 1))
        with patch('apps.common.validators.timezone.now', return_value=frozen_now):
            with self.assertRaisesMessage(ValidationError, 'You cannot book dates in the past.'):
                validate_booking_dates(check_in, check_out)

    def test_valid_future_dates_pass(self):
        check_in = date(2024, 1, 2)
        check_out = date(2024, 1, 5)
        frozen_now = timezone.make_aware(datetime(2024, 1, 1))
        with patch('apps.common.validators.timezone.now', return_value=frozen_now):
            validate_booking_dates(check_in, check_out)


class ValidateReviewAfterStayTests(SimpleTestCase):
    def test_cannot_review_before_checkout(self):
        booking = SimpleNamespace(check_out=date(2024, 1, 5))
        frozen_now = timezone.make_aware(datetime(2024, 1, 1))
        with patch('apps.common.validators.timezone.now', return_value=frozen_now):
            with self.assertRaisesMessage(ValidationError, 'You cannot leave a review before your stay ends on 2024-01-05.'):
                validate_review_after_stay(booking)

    def test_can_review_after_checkout(self):
        booking = SimpleNamespace(check_out=date(2024, 1, 5))
        frozen_now = timezone.make_aware(datetime(2024, 1, 6))
        with patch('apps.common.validators.timezone.now', return_value=frozen_now):
            validate_review_after_stay(booking)


class ValidateMaxGuestsPerRoomTests(SimpleTestCase):
    def test_exceeding_guests_raises_error(self):
        with self.assertRaisesMessage(ValidationError, 'Number of guests (5) exceeds maximum allowed (4).'):
            validate_max_guests_per_room(num_guests=5, max_guests=4)

    def test_maximum_boundary_is_allowed(self):
        validate_max_guests_per_room(num_guests=4, max_guests=4)
