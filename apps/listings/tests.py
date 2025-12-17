from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from apps.common.enums import PropertyType, CancellationPolicy, UserRole
from apps.common.models import Location
from apps.listings.models import Listing
from apps.users.models import User


class ListingVisibilityTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner_1 = User.objects.create_user(
            username='owner1',
            email='owner1@example.com',
            password='password123',
            role=UserRole.OWNER,
        )
        self.owner_2 = User.objects.create_user(
            username='owner2',
            email='owner2@example.com',
            password='password123',
            role=UserRole.OWNER,
        )

        self.listing_1 = self._create_listing(self.owner_1, 'Central flat', 'Address 1')
        self.listing_2 = self._create_listing(self.owner_1, 'Cozy loft', 'Address 2')
        self.listing_3 = self._create_listing(self.owner_2, 'Beach house', 'Address 3')

    def _create_listing(self, owner, title, address):
        location = Location.objects.create(
            country='Ukraine',
            city='Kyiv',
            address=address,
        )
        return Listing.objects.create(
            owner=owner,
            title=title,
            description='Test listing',
            property_type=PropertyType.APARTMENT,
            location=location,
            is_hotel_apartment=False,
            num_rooms=1,
            num_bedrooms=1,
            num_bathrooms=1,
            max_guests=2,
            area=Decimal('25.00'),
            price=Decimal('80.00'),
            cancellation_policy=CancellationPolicy.FLEXIBLE,
        )

    def _get_results(self, response):
        return response.data['results'] if isinstance(response.data, dict) and 'results' in response.data else response.data

    def test_filter_by_owner_returns_only_owner_listings(self):
        response = self.client.get('/api/listings/', {'owner': self.owner_1.id})

        self.assertEqual(response.status_code, 200)
        results = self._get_results(response)
        returned_titles = {listing['title'] for listing in results}

        self.assertSetEqual(returned_titles, {self.listing_1.title, self.listing_2.title})
        for listing in results:
            self.assertEqual(listing['owner'], self.owner_1.id)
            self.assertIn('owner_name', listing)

    def test_public_detail_includes_owner_info(self):
        response = self.client.get(f'/api/listings/{self.listing_1.id}/')

        self.assertEqual(response.status_code, 200)
        self.assertIn('owner_info', response.data)
        self.assertEqual(response.data['owner_info']['id'], self.owner_1.id)
        self.assertEqual(response.data['owner_info']['name'], self.owner_1.get_full_name() or self.owner_1.email)
