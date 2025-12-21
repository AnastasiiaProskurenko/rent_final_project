from decimal import Decimal
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.users.models import User
from apps.common.enums import UserRole, PropertyType, CancellationPolicy
from apps.common.models import Location
from apps.listings.models import Listing, ListingPrice
from apps.bookings.models import Booking


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
