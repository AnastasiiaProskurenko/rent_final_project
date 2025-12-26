from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.bookings.models import Booking
from apps.common.enums import (
    BookingStatus,
    CancellationPolicy,
    PaymentStatus,
    PropertyType,
)
from apps.common.models import Location
from apps.listings.models import Listing, ListingPrice
from apps.notifications.models import Notification


class BookingNotificationTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.customer = User.objects.create_user(
            email='customer@example.com',
            username='customer',
            first_name='Customer',
            last_name='Test',
            password='password123',
        )
        self.owner = User.objects.create_user(
            email='owner@example.com',
            username='owner',
            first_name='Owner',
            last_name='Test',
            password='password123',
        )
        self.location = Location.objects.create(
            country='Україна',
            city='Київ',
            address='вул. Хрещатик 1',
        )
        self.listing = Listing.objects.create(
            owner=self.owner,
            title='Простора квартира в центрі міста',
            description='Дуже довгий опис квартири, що перевищує мінімальну довжину.',
            location=self.location,
            property_type=PropertyType.APARTMENT,
            num_rooms=1,
            num_bathrooms=1,
            max_guests=2,
            price=Decimal('100.00'),
            cancellation_policy=CancellationPolicy.FLEXIBLE,
        )
        self.listing_price = ListingPrice.objects.create(
            listing=self.listing,
            amount=Decimal('100.00'),
        )

    def _create_booking(self, status=BookingStatus.PENDING):
        return Booking.objects.create(
            customer=self.customer,
            listing=self.listing,
            location=self.location,
            check_in=date.today() + timedelta(days=1),
            check_out=date.today() + timedelta(days=2),
            num_guests=1,
            price_per_night=self.listing_price,
            num_nights=1,
            base_price=Decimal('100.00'),
            cleaning_fee=Decimal('0.00'),
            platform_fee=Decimal('10.00'),
            total_price=Decimal('110.00'),
            status=status,
            payment_status=PaymentStatus.PENDING,
            special_requests='',
            cancellation_policy=CancellationPolicy.FLEXIBLE,
        )

    def test_notifications_created_on_booking_creation(self):
        booking = self._create_booking()

        customer_notifications = Notification.objects.filter(
            user=self.customer,
            related_object_type='booking',
        )
        owner_notifications = Notification.objects.filter(
            user=self.owner,
            related_object_type='booking',
        )

        self.assertEqual(customer_notifications.count(), 1)
        self.assertEqual(owner_notifications.count(), 1)

        self.assertEqual(
            customer_notifications.first().message,
            f'Бронювання #{booking.pk} створено, чекайте підтвердження',
        )
        self.assertEqual(
            owner_notifications.first().message,
            f'Новий букінг #{booking.pk}, прийміть або скасуйте',
        )

    def test_notification_created_on_status_change(self):
        booking = self._create_booking()
        Notification.objects.all().delete()

        for new_status, expected_text in [
            (BookingStatus.CONFIRMED, 'підтверджено'),
            (BookingStatus.CANCELLED, 'скасовано'),
        ]:
            with self.subTest(new_status=new_status):
                booking.status = new_status
                booking.save(update_fields=['status'])

                notifications = Notification.objects.filter(
                    user=self.customer,
                    related_object_type='booking',
                )
                self.assertEqual(notifications.count(), 1)
                self.assertEqual(
                    notifications.first().message,
                    f'Бронювання #{booking.pk} {expected_text}.',
                )

                Notification.objects.all().delete()
