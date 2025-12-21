from datetime import date, datetime, timedelta
from datetime import date, datetime
from types import SimpleNamespace
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import SimpleTestCase, TestCase
from django.utils import timezone

from apps.common.models import Location
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


class TimeModelTests(TestCase):
    def setUp(self):
        self.location = Location.objects.create(
            country=' Ukraine ',
            city=' Lviv ',
            address=' Shevchenka street '
        )

    def test_is_deleted_defaults_false(self):
        self.assertFalse(self.location.is_deleted)

    def test_created_at_is_set_on_creation(self):
        self.assertIsNotNone(self.location.created_at)
        self.assertTrue(timezone.is_aware(self.location.created_at))

    def test_updated_at_changes_on_save(self):
        first_updated = self.location.updated_at
        self.location.address = 'New address 10'
        self.location.save()
        self.assertGreater(self.location.updated_at, first_updated)

    def test_deleted_at_is_none_by_default(self):
        self.assertIsNone(self.location.deleted_at)

    def test_soft_delete_sets_deleted_flags(self):
        self.location.soft_delete()
        self.location.refresh_from_db()
        self.assertTrue(self.location.is_deleted)
        self.assertIsNotNone(self.location.deleted_at)

    def test_soft_delete_persists_to_database(self):
        self.location.soft_delete()
        fetched = Location.objects.get(pk=self.location.pk)
        self.assertTrue(fetched.is_deleted)
        self.assertIsNotNone(fetched.deleted_at)

    def test_soft_delete_updates_deleted_at_each_call(self):
        self.location.soft_delete()
        first_deleted = self.location.deleted_at
        self.location.soft_delete()
        self.assertGreater(self.location.deleted_at, first_deleted)

    def test_soft_delete_keeps_created_at_unchanged(self):
        created_at = self.location.created_at
        self.location.soft_delete()
        self.location.refresh_from_db()
        self.assertEqual(self.location.created_at, created_at)

    def test_soft_delete_uses_timezone_aware_timestamp(self):
        self.location.soft_delete()
        self.assertTrue(timezone.is_aware(self.location.deleted_at))

    def test_save_updates_timestamp_when_fields_change(self):
        initial_updated = self.location.updated_at
        later_time = initial_updated + timedelta(minutes=1)
        with patch('django.utils.timezone.now', return_value=later_time):
            self.location.city = 'Kyiv'
            self.location.save()
        self.location.refresh_from_db()
        self.assertGreater(self.location.updated_at, initial_updated)


class LocationModelTests(TestCase):
    def test_normalize_address_removes_extra_spaces(self):
        normalized = Location.normalize_address('  Main   street   1  ')
        self.assertEqual(normalized, 'main street 1')

    def test_normalize_address_handles_empty_values(self):
        self.assertEqual(Location.normalize_address(''), '')
        self.assertEqual(Location.normalize_address(None), '')

    def test_normalize_address_replaces_common_terms(self):
        normalized = Location.normalize_address('вулиця Шевченка будинок 5, кв 2')
        self.assertIn('вул', normalized)
        self.assertIn('буд', normalized)
        self.assertIn('кв', normalized)

    def test_save_trims_fields_and_sets_normalized(self):
        location = Location.objects.create(
            country=' Poland ',
            city=' Warsaw ',
            address='   Marszałkowska 10  '
        )
        self.assertEqual(location.country, 'Poland')
        self.assertEqual(location.city, 'Warsaw')
        self.assertEqual(location.address, 'Marszałkowska 10')
        self.assertEqual(location.normalized_address, 'marszałkowska 10')

    def test_str_representation_includes_address_city_country(self):
        location = Location.objects.create(
            country='Germany',
            city='Berlin',
            address='Unter den Linden 1'
        )
        self.assertEqual(str(location), 'Unter den Linden 1, Berlin, Germany')

    def test_ordering_by_city_then_country(self):
        kyiv = Location.objects.create(country='Ukraine', city='Kyiv', address='X')
        lviv = Location.objects.create(country='Ukraine', city='Lviv', address='Y')
        locations = list(Location.objects.all())
        self.assertEqual(locations[0], kyiv)
        self.assertEqual(locations[1], lviv)

    def test_unique_constraint_on_normalized_address(self):
        Location.objects.create(country='Ukraine', city='Kyiv', address='Main St 1')
        with self.assertRaises(IntegrityError):
            Location.objects.create(country='Ukraine', city='Kyiv', address='  main   st 1 ')

    def test_latitude_and_longitude_are_optional(self):
        location = Location.objects.create(country='France', city='Paris', address='Rue 1')
        self.assertIsNone(location.latitude)
        self.assertIsNone(location.longitude)

    def test_normalize_address_removes_periods(self):
        normalized = Location.normalize_address('St. Andrew St.')
        self.assertEqual(normalized, 'st andrew st')

    def test_normalized_address_persists_on_save(self):
        location = Location.objects.create(country='Italy', city='Rome', address='Via Roma 12')
        location.address = 'Via Roma 12   '
        location.save()
        location.refresh_from_db()
        self.assertEqual(location.normalized_address, 'via roma 12')

    def test_normalize_address_handles_multiple_replacements(self):
        normalized = Location.normalize_address(' проспект Перемоги буд 10 квартира 5 ')
        self.assertEqual(normalized, 'просп перемоги буд10 кв5')
