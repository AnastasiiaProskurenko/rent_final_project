from decimal import Decimal
from datetime import timedelta
import io
from contextlib import redirect_stdout
import logging

from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.users.models import RefreshTokenRecord, User, UserProfile
from apps.common.enums import UserRole, PropertyType, CancellationPolicy
from apps.common.models import Location
from apps.listings.models import Listing, ListingPrice
from apps.bookings.models import Booking
from apps.notifications.models import Notification


class UserVisibilityTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='password123',
            role=UserRole.ADMIN,
        )
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='password123',
            role=UserRole.OWNER,
        )
        self.customer = User.objects.create_user(
            username='customer',
            email='customer@example.com',
            password='password123',
            role=UserRole.CUSTOMER,
        )
        self.other_customer = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='password123',
            role=UserRole.CUSTOMER,
        )

        location = Location.objects.create(
            country='Ukraine',
            city='Kyiv',
            address='Main street 1'
        )
        listing = Listing.objects.create(
            owner=self.owner,
            title='Owner flat',
            description='Nice place',
            property_type=PropertyType.APARTMENT,
            location=location,
            is_hotel_apartment=False,
            num_rooms=1,
            num_bedrooms=1,
            num_bathrooms=1,
            max_guests=2,
            area=Decimal('30.00'),
            price=Decimal('50.00'),
            cancellation_policy=CancellationPolicy.FLEXIBLE,
        )
        price_record = ListingPrice.objects.create(
            listing=listing,
            amount=listing.price
        )
        Booking.objects.create(
            customer=self.customer,
            listing=listing,
            location=location,
            check_in=timezone.now().date() + timedelta(days=1),
            check_out=timezone.now().date() + timedelta(days=2),
            num_guests=1,
            price_per_night=price_record,
            num_nights=1,
            base_price=price_record.amount,
            cleaning_fee=Decimal('0.00'),
            platform_fee=Decimal('0.00'),
            total_price=price_record.amount,
            cancellation_policy=CancellationPolicy.FLEXIBLE,
            special_requests='',
        )

    def _get_results(self, response):
        return response.data['results'] if isinstance(response.data, dict) and 'results' in response.data else response.data

    def test_admin_sees_all_users(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/users/')

        self.assertEqual(response.status_code, 200)
        results = self._get_results(response)
        self.assertEqual(len(results), 4)

    def test_owner_sees_only_related_customers(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.get('/api/users/')

        self.assertEqual(response.status_code, 200)
        results = self._get_results(response)
        returned_emails = {user['email'] for user in results}
        self.assertSetEqual(
            returned_emails,
            {self.owner.email, self.customer.email}
        )

    def test_customer_sees_only_self(self):
        self.client.force_authenticate(user=self.other_customer)
        response = self.client.get('/api/users/')

        self.assertEqual(response.status_code, 200)
        results = self._get_results(response)
        returned_emails = [user['email'] for user in results]
        self.assertEqual(returned_emails, [self.other_customer.email])


class UserAuthApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='apitester',
            email='apitester@example.com',
            password='strong-pass-123',
            role=UserRole.CUSTOMER,
        )

    def test_obtain_token_with_valid_credentials(self):
        response = self.client.post(
            '/api/auth/token/',
            {'email': 'apitester@example.com', 'password': 'strong-pass-123'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_obtain_token_rejects_invalid_credentials(self):
        response = self.client.post(
            '/api/auth/token/',
            {'email': 'apitester@example.com', 'password': 'wrong-pass'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_protected_endpoint_with_token(self):
        token_response = self.client.post(
            '/api/auth/token/',
            {'email': 'apitester@example.com', 'password': 'strong-pass-123'},
            format='json'
        )
        access_token = token_response.data['access']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get('/api/users/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results'] if 'results' in response.data else response.data
        returned_emails = [user['email'] for user in results]
        self.assertIn(self.user.email, returned_emails)


class UserModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='baseuser',
            email='base@example.com',
            password='strong-pass-123',
            first_name='Base',
            last_name='User',
        )

    def test_email_is_unique(self):
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username='duplicate',
                email='base@example.com',
                password='another-pass',
            )

    def test_default_role_is_customer(self):
        self.assertTrue(self.user.is_customer())
        self.assertEqual(self.user.role, UserRole.CUSTOMER)

    def test_get_full_name_combines_first_and_last(self):
        self.assertEqual(self.user.get_full_name(), 'Base User')

    def test_get_full_name_falls_back_to_username(self):
        self.user.first_name = ''
        self.user.last_name = ''
        self.user.save()
        self.assertEqual(self.user.get_full_name(), self.user.username)

    def test_is_owner_helper(self):
        self.user.role = UserRole.OWNER
        self.user.save()
        self.assertTrue(self.user.is_owner())
        self.assertFalse(self.user.is_customer())

    def test_is_admin_true_for_admin_role(self):
        self.user.role = UserRole.ADMIN
        self.user.save()
        self.assertTrue(self.user.is_admin())

    def test_is_admin_true_for_superuser(self):
        superuser = User.objects.create_superuser(
            username='super',
            email='super@example.com',
            password='super-pass',
        )
        self.assertTrue(superuser.is_admin())

    def test_string_representation_includes_role_display(self):
        self.assertIn(self.user.get_role_display(), str(self.user))

    def test_username_field_is_email_for_auth(self):
        self.assertEqual(User.USERNAME_FIELD, 'email')

    def test_role_changes_persist(self):
        self.user.role = UserRole.OWNER
        self.user.save(update_fields=['role'])
        reloaded = User.objects.get(pk=self.user.pk)
        self.assertEqual(reloaded.role, UserRole.OWNER)


class UserSignalTests(TestCase):
    def test_system_notification_created_on_user_creation(self):
        buffer = io.StringIO()
        logger_name = 'apps.users.signals'
        with self.assertLogs(logger_name, level='INFO') as captured_logs, redirect_stdout(buffer):
            user = User.objects.create_user(
                username='notifieduser',
                email='notify@example.com',
                password='notify-pass',
                first_name='Notify',
                last_name='User',
            )

        notifications = Notification.objects.filter(user=user)

        self.assertEqual(notifications.count(), 1)
        notification = notifications.first()
        self.assertEqual(notification.notification_type, 'SYSTEM')
        self.assertEqual(notification.title, 'User Notify User створений')
        self.assertEqual(notification.message, 'User Notify User створений')
        self.assertIn('User Notify User створений', buffer.getvalue())
        self.assertIn('User Notify User створений', '\n'.join(captured_logs.output))


class UserProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='profileuser',
            email='profile@example.com',
            password='profile-pass',
            role=UserRole.OWNER,
        )
        self.profile = UserProfile.objects.create(user=self.user)
        self.location = Location.objects.create(
            country='Ukraine', city='Kyiv', address='Main 1'
        )

    def test_listing_count_only_counts_active_non_deleted(self):
        Listing.objects.create(
            owner=self.user,
            title='Active listing',
            description='Great place',
            property_type=PropertyType.APARTMENT,
            location=self.location,
            is_hotel_apartment=False,
            num_rooms=1,
            num_bedrooms=1,
            num_bathrooms=1,
            max_guests=2,
            area=Decimal('20.00'),
            price=Decimal('30.00'),
            cancellation_policy=CancellationPolicy.FLEXIBLE,
        )
        inactive = Listing.objects.create(
            owner=self.user,
            title='Inactive listing',
            description='Closed',
            property_type=PropertyType.APARTMENT,
            location=self.location,
            is_hotel_apartment=False,
            num_rooms=1,
            num_bedrooms=1,
            num_bathrooms=1,
            max_guests=2,
            area=Decimal('25.00'),
            price=Decimal('40.00'),
            cancellation_policy=CancellationPolicy.MODERATE,
            is_active=False,
        )
        inactive.soft_delete()

        self.assertEqual(self.profile.listing_count, 1)

    def test_rating_defaults_to_zero_when_no_reviews(self):
        self.assertEqual(self.profile.rating, 0.0)

    def test_string_representation_uses_user_display(self):
        self.assertIn(self.user.get_role_display(), str(self.profile))

    def test_phone_allows_blank_values(self):
        self.profile.phone = ''
        self.profile.save()
        reloaded = self.user.profile
        self.assertEqual(reloaded.phone, '')

    def test_languages_default_value(self):
        self.assertEqual(self.profile.languages, 'de')


class RefreshTokenRecordTests(TestCase):
    def test_revoke_marks_token_as_revoked(self):
        user = User.objects.create_user(
            username='tokenuser',
            email='token@example.com',
            password='token-pass',
        )
        record = RefreshTokenRecord.objects.create(
            user=user,
            jti='token-jti-1',
            token='sample-token',
        )

        record.revoke()
        record.refresh_from_db()
        self.assertTrue(record.revoked)
