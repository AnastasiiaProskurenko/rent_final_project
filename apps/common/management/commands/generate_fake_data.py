from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction
from faker import Faker
import random
from decimal import Decimal

from apps.listings.models import Listing
from apps.bookings.models import Booking
from apps.reviews.models import Review

User = get_user_model()
fake = Faker(['en_US'])


class Command(BaseCommand):
    help = 'Generate minimal fake data for testing'

    def add_arguments(self, parser):
        parser.add_argument('--users', type=int, default=20)
        parser.add_argument('--listings', type=int, default=50)
        parser.add_argument('--bookings', type=int, default=30)
        parser.add_argument('--reviews', type=int, default=20)
        parser.add_argument('--password', type=str, default='1111')
        parser.add_argument('--clear', action='store_true')

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing data...')
            Review.objects.all().delete()
            Booking.objects.all().delete()
            Listing.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()

        with transaction.atomic():
            self.stdout.write('Generating fake data...')

            groups = self.create_groups()
            users = self.generate_users(options['users'], options['password'], groups)
            self.stdout.write(f'✓ {len(users)} users')

            listings = self.generate_listings(options['listings'], users)
            self.stdout.write(f'✓ {len(listings)} listings')

            bookings = self.generate_bookings(options['bookings'], users, listings)
            self.stdout.write(f'✓ {len(bookings)} bookings')

            reviews = self.generate_reviews(options['reviews'], bookings)
            self.stdout.write(f'✓ {len(reviews)} reviews')

        self.stdout.write(self.style.SUCCESS('\n✅ Done!'))
        self.stdout.write(f'Password for all users: {options["password"]}')

    def create_groups(self):
        groups = {}
        for name in ['Customers', 'Owners', 'Admins']:
            groups[name], _ = Group.objects.get_or_create(name=name)
        return groups

    def generate_users(self, count, password, groups):
        users = []
        for i in range(count):
            rand = random.random()
            if rand < 0.30:
                user_type, group = 'owner', groups['Owners']
            elif rand < 0.95:
                user_type, group = 'customer', groups['Customers']
            else:
                user_type, group = 'admin', groups['Admins']

            user = User.objects.create_user(
                username=f"{user_type}_{i + 1}",
                email=f"{user_type}_{i + 1}@example.com",
                password=password,
                first_name=fake.first_name(),
                last_name=fake.last_name()
            )
            user.groups.add(group)
            users.append(user)
        return users

    def generate_listings(self, count, users):
        owners = [u for u in users if u.groups.filter(name='Owners').exists()] or users
        listings = []
        cities = ['Berlin', 'Munich', 'Hamburg', 'Cologne', 'Frankfurt']

        for i in range(count):
            listings.append(Listing.objects.create(
                owner=random.choice(owners),
                title=f"{random.choice(['Apartment', 'House', 'Studio'])} in {random.choice(cities)}",
                description=fake.text(200),
                listing_type=random.choice(['apartment', 'house', 'studio']),
                address=fake.street_address(),
                city=random.choice(cities),
                country='Germany',
                price=Decimal(random.randint(50, 500)),
                bedrooms=random.randint(1, 4),
                bathrooms=random.randint(1, 2),
                max_guests=random.randint(2, 8),
                is_active=True
            ))
        return listings

    def generate_bookings(self, count, users, listings):
        customers = [u for u in users if u.groups.filter(name='Customers').exists()] or users
        bookings = []

        for i in range(count):
            listing = random.choice(listings)
            customer = random.choice([c for c in customers if c != listing.owner] or customers)
            start = fake.date_between(start_date='-30d', end_date='+30d')
            end = fake.date_between(start_date=start, end_date='+60d')
            nights = (end - start).days or 1

            bookings.append(Booking.objects.create(
                listing=listing,
                customer=customer,
                check_in=start,
                check_out=end,
                num_guests=random.randint(1, listing.max_guests),
                total_price=listing.price * nights,
                status=random.choice(['pending', 'confirmed', 'completed', 'cancelled']),
                created_by=customer
            ))
        return bookings

    def generate_reviews(self, count, bookings):
        completed = [b for b in bookings if b.status == 'completed']
        if not completed:
            for b in bookings[:min(20, len(bookings))]:
                b.status = 'completed'
                b.save()
                completed.append(b)

        reviews = []
        used = set()
        for i in range(min(count, len(completed))):
            available = [b for b in completed if b.id not in used]
            if not available:
                break
            booking = random.choice(available)
            used.add(booking.id)

            reviews.append(Review.objects.create(
                booking=booking,
                listing=booking.listing,
                reviewer=booking.customer,
                rating=random.randint(3, 5),
                comment=fake.text(200) if random.choice([True, False]) else None
            ))
        return reviews
