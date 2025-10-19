from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from faker import Faker
import random
from datetime import datetime, timedelta
from decimal import Decimal

from apps.listings.models import Listing, ListingPhoto
from apps.bookings.models import Booking
from apps.reviews.models import Review, OwnerRating
from apps.notifications.models import Notification
from apps.payments.models import Payment, Refund
from apps.search.models import SearchQuery, SearchHistory
from apps.analytics.models import ListingView
from apps.common.enums import Role, BookingStatus, NotificationType, PaymentMethod

User = get_user_model()
fake = Faker(['en_US', 'de_DE', 'ru_RU'])


class Command(BaseCommand):
    help = 'Generate fake data for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=50,
            help='Number of users to create (default: 50)'
        )
        parser.add_argument(
            '--listings',
            type=int,
            default=100,
            help='Number of listings to create (default: 100)'
        )
        parser.add_argument(
            '--bookings',
            type=int,
            default=200,
            help='Number of bookings to create (default: 200)'
        )
        parser.add_argument(
            '--reviews',
            type=int,
            default=150,
            help='Number of reviews to create (default: 150)'
        )
        parser.add_argument(
            '--notifications',
            type=int,
            default=200,
            help='Number of notifications to create (default: 200)'
        )
        parser.add_argument(
            '--payments',
            type=int,
            default=100,
            help='Number of payments to create (default: 100)'
        )
        parser.add_argument(
            '--search-queries',
            type=int,
            default=300,
            help='Number of search queries to create (default: 300)'
        )
        parser.add_argument(
            '--listing-views',
            type=int,
            default=500,
            help='Number of listing views to create (default: 500)'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='1111',
            help='Common password for all users (default: 1111)'
        )
        parser.add_argument(
            '--unique-passwords',
            action='store_true',
            help='Generate unique passwords for each user instead of common password'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before generating new data'
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            self.clear_data()

        with transaction.atomic():
            self.stdout.write('Generating fake data...')
            

            users = self.generate_users(options['users'], options['password'], options['unique_passwords'])
            self.stdout.write(f'Created {len(users)} users')
            

            listings = self.generate_listings(options['listings'], users)
            self.stdout.write(f'Created {len(listings)} listings')
            

            bookings = self.generate_bookings(options['bookings'], users, listings)
            self.stdout.write(f'Created {len(bookings)} bookings')
            

            reviews = self.generate_reviews(options['reviews'], bookings)
            self.stdout.write(f'Created {len(reviews)} reviews')
            

            owner_ratings = self.generate_owner_ratings(users)
            self.stdout.write(f'Created {len(owner_ratings)} owner ratings')
            

            notifications = self.generate_notifications(options['notifications'], users, bookings)
            self.stdout.write(f'Created {len(notifications)} notifications')
            

            payments = self.generate_payments(options['payments'], bookings, users)
            self.stdout.write(f'Created {len(payments)} payments')
            

            search_queries = self.generate_search_queries(options['search_queries'], users)
            self.stdout.write(f'Created {len(search_queries)} search queries')
            

            listing_views = self.generate_listing_views(options['listing_views'], users, listings)
            self.stdout.write(f'Created {len(listing_views)} listing views')

        self.stdout.write(
            self.style.SUCCESS('Successfully generated fake data!')
        )
        

        if hasattr(self, 'user_passwords'):

            self.stdout.write('')
            self.stdout.write(self.style.WARNING('Generated user credentials:'))
            self.stdout.write('=' * 50)
            for username, password in list(self.user_passwords.items())[:10]:
                self.stdout.write(f'{username}: {password}')
            if len(self.user_passwords) > 10:
                self.stdout.write(f'... and {len(self.user_passwords) - 10} more users')
            self.stdout.write('=' * 50)
        else:

            self.stdout.write('')
            self.stdout.write(self.style.WARNING('User credentials:'))
            self.stdout.write('=' * 50)
            self.stdout.write(f'All users password: {options["password"]}')
            self.stdout.write('')
            self.stdout.write('Sample users:')
            self.stdout.write('owner_1, owner_2, ... (30% of users)')
            self.stdout.write('customer_1, customer_2, ... (70% of users)')
            self.stdout.write('=' * 50)

    def clear_data(self):

        from django.db import connection
        

        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            existing_tables = [row[0] for row in cursor.fetchall()]
        

        if 'payments_refund' in existing_tables:
            Refund.objects.all().delete()
        if 'payments_payment' in existing_tables:
            Payment.objects.all().delete()
        if 'notifications_notification' in existing_tables:
            Notification.objects.all().delete()
        if 'analytics_listingview' in existing_tables:
            ListingView.objects.all().delete()
        if 'search_searchhistory' in existing_tables:
            SearchHistory.objects.all().delete()
        if 'search_searchquery' in existing_tables:
            SearchQuery.objects.all().delete()
        if 'reviews_review' in existing_tables:
            Review.objects.all().delete()
        if 'reviews_ownerrating' in existing_tables:
            OwnerRating.objects.all().delete()
        if 'bookings_booking' in existing_tables:
            Booking.objects.all().delete()
        if 'listings_listingphoto' in existing_tables:
            ListingPhoto.objects.all().delete()
        if 'listings_listing' in existing_tables:
            Listing.objects.all().delete()
        if 'users_user' in existing_tables:
            User.objects.filter(is_superuser=False).delete()

    def generate_users(self, count, common_password, unique_passwords):

        users = []
        passwords = []
        

        owner_count = int(count * 0.3)
        customer_count = count - owner_count
        
        self.stdout.write(f'Creating {owner_count} owners and {customer_count} customers...')
        

        from apps.users.models import UserProfile
        

        if unique_passwords:
            for i in range(count):

                password_patterns = [
                    lambda: f"{fake.word().capitalize()}{random.randint(100, 999)}{fake.word().capitalize()}",
                    lambda: f"{fake.word()}_{random.randint(10, 99)}_{fake.word()}",
                    lambda: f"{fake.word()}{random.choice('!@#$%^&*')}{random.randint(1000, 9999)}",
                    lambda: f"{fake.word().capitalize()}{random.choice('!@#$%^&*')}{fake.word()}{random.randint(10, 99)}",
                    lambda: f"{random.randint(100, 999)}{fake.word().capitalize()}{random.choice('!@#$%^&*')}{fake.word()}",
                ]
                password = random.choice(password_patterns)()
                passwords.append(password)
        else:
            passwords = [common_password] * count
        

        for i in range(owner_count):
            user_password = passwords[i] if unique_passwords else common_password
            user = User.objects.create_user(
                username=f'owner_{i+1}',
                email=f'owner{i+1}@example.com',
                password=user_password,
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                role=Role.OWNER,
                is_verified=True,
                is_active=True
            )
            users.append(user)
            

            UserProfile.objects.create(
                user=user,
                phone=fake.phone_number()[:30] if random.choice([True, False]) else None,
                biography=fake.text(max_nb_chars=500) if random.choice([True, False]) else None,
                languages=random.choice(['de', 'en', 'ru', 'de,en', 'en,ru'])
            )
        

        for i in range(customer_count):
            user_password = passwords[owner_count + i] if unique_passwords else common_password
            user = User.objects.create_user(
                username=f'customer_{i+1}',
                email=f'customer{i+1}@example.com',
                password=user_password,
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                role=Role.CUSTOMER,
                is_verified=random.choice([True, False]),
                is_active=True
            )
            users.append(user)
            

            UserProfile.objects.create(
                user=user,
                phone=fake.phone_number()[:30] if random.choice([True, False]) else None,
                biography=fake.text(max_nb_chars=500) if random.choice([True, False]) else None,
                languages=random.choice(['de', 'en', 'ru', 'de,en', 'en,ru'])
            )
        

        if unique_passwords:
            self.user_passwords = dict(zip([u.username for u in users], passwords))
            
        return users

    def generate_listings(self, count, users):

        listings = []
        owners = [u for u in users if u.role in [Role.OWNER, Role.MANAGER]]
        
        if not owners:

            for i in range(min(10, len(users))):
                users[i].role = Role.OWNER
                users[i].save()
            owners = users[:10]
        
        amenities = [
            'has_air_conditioning', 'has_tv', 'has_minibar', 'has_fridge',
            'has_kitchen', 'has_bathroom', 'has_washing_machine',
            'has_hair_dryer', 'hygiene_products', 'has_parking'
        ]
        
        cities = [
            'Berlin', 'Munich', 'Hamburg', 'Cologne', 'Frankfurt',
            'Stuttgart', 'Düsseldorf', 'Dortmund', 'Essen', 'Leipzig'
        ]
        
        for i in range(count):
            owner = random.choice(owners)
            
            listing = Listing.objects.create(
                owner=owner,
                title=fake.catch_phrase(),
                description=fake.text(max_nb_chars=1000),
                price=Decimal(str(round(random.uniform(30, 500), 2))),
                num_rooms=random.randint(1, 5),
                max_guests=random.randint(1, 8),
                pets_allowed=random.choice([True, False]),
                country='Germany',
                city=random.choice(cities),
                district=fake.city_suffix() if random.choice([True, False]) else None,
                street=fake.street_name(),
                house_number=str(random.randint(1, 200)),
                apartment_number=str(random.randint(1, 50)) if random.choice([True, False]) else None,
                distance_to_center=round(random.uniform(0.5, 20), 1) if random.choice([True, False]) else None,
                distance_to_sea=round(random.uniform(1, 100), 1) if random.choice([True, False]) else None,
                category=random.choice(['apartment', 'house', 'studio', 'villa', 'loft']),
                is_active=random.choice([True, False])
            )
            

            for amenity in amenities:
                value = random.choice([True, False, None])
                setattr(listing, amenity, value)
            listing.save()
            
            listings.append(listing)
            
        return listings

    def generate_bookings(self, count, users, listings):

        bookings = []
        customers = [u for u in users if u.role == Role.CUSTOMER]
        active_listings = [l for l in listings if l.is_active]
        
        if not customers:
            customers = users[:10]
        if not active_listings:
            active_listings = listings[:10]
        
        statuses = [BookingStatus.WAITING, BookingStatus.AGREED, 
                   BookingStatus.CANCELED, BookingStatus.ENDED]
        
        for i in range(count):
            customer = random.choice(customers)
            listing = random.choice(active_listings)
            

            start_date = fake.date_between(start_date='-30d', end_date='+60d')
            end_date = start_date + timedelta(days=random.randint(1, 14))
            
            booking = Booking.objects.create(
                customer=customer,
                listing=listing,
                check_in=start_date,
                check_out=end_date,
                num_guests=random.randint(1, min(8, listing.max_guests)),
                status=random.choice(statuses),
                notes=fake.text(max_nb_chars=200) if random.choice([True, False]) else None,
                created_by=customer
            )
            
            bookings.append(booking)
            
        return bookings

    def generate_reviews(self, count, bookings):

        reviews = []
        ended_bookings = [b for b in bookings if b.status == BookingStatus.ENDED]
        
        if not ended_bookings:

            for booking in bookings[:min(50, len(bookings))]:
                booking.status = BookingStatus.ENDED
                booking.check_out = fake.date_between(start_date='-30d', end_date='-1d')
                booking.save()
                ended_bookings.append(booking)
        
        for i in range(min(count, len(ended_bookings))):
            booking = random.choice(ended_bookings)
            

            if hasattr(booking, 'review'):
                continue
                
            review = Review.objects.create(
                booking=booking,
                listing=booking.listing,
                customer=booking.customer,
                rating=random.randint(1, 5),
                comment=fake.text(max_nb_chars=500) if random.choice([True, False]) else None,
                owner_comment=fake.text(max_nb_chars=300) if random.choice([True, False]) else None
            )
            
            reviews.append(review)
            
        return reviews

    def generate_owner_ratings(self, users):

        ratings = []
        owners = [u for u in users if u.role in [Role.OWNER, Role.MANAGER]]
        customers = [u for u in users if u.role == Role.CUSTOMER]
        
        if not owners or not customers:
            return ratings
        
        for owner in owners[:10]:
            for _ in range(random.randint(1, 5)):
                customer = random.choice(customers)
                

                if OwnerRating.objects.filter(owner=owner, rater=customer).exists():
                    continue
                    
                rating = OwnerRating.objects.create(
                    owner=owner,
                    rater=customer,
                    rating=random.randint(1, 5)
                )
                
                ratings.append(rating)
                
        return ratings

    def generate_notifications(self, count, users, bookings):

        notifications = []
        notification_types = [NotificationType.BOOKING_CREATED, NotificationType.BOOKING_CONFIRMED, 
                            NotificationType.BOOKING_REMINDER, NotificationType.REVIEW_REQUEST, 
                            NotificationType.NEW_REVIEW]
        
        for i in range(count):
            user = random.choice(users)
            notification_type = random.choice(notification_types)
            

            if notification_type == NotificationType.BOOKING_CREATED:
                title = "New Booking Request"
                message = f"You have received a new booking request for your property."
            elif notification_type == NotificationType.BOOKING_CONFIRMED:
                title = "Booking Confirmed"
                message = f"Your booking has been confirmed. Check your booking details."
            elif notification_type == NotificationType.BOOKING_REMINDER:
                title = "Booking Reminder"
                message = f"Your booking starts tomorrow. Don't forget to check in!"
            elif notification_type == NotificationType.REVIEW_REQUEST:
                title = "Review Request"
                message = f"Please leave a review for your recent stay."
            else:
                title = "New Review"
                message = f"You have received a new review for your property."
            
            notification = Notification.objects.create(
                user=user,
                type=notification_type,
                title=title,
                message=message,
                is_read=random.choice([True, False]),
                related_object_id=random.randint(1, 100) if random.choice([True, False]) else None,
                related_object_type=random.choice(['booking', 'listing', 'review']) if random.choice([True, False]) else None
            )
            
            notifications.append(notification)
            
        return notifications

    def generate_payments(self, count, bookings, users):

        payments = []
        payment_methods = [PaymentMethod.CREDIT_CARD, PaymentMethod.PAYPAL, 
                          PaymentMethod.APPLE_PAY, PaymentMethod.GOOGLE_PAY, 
                          PaymentMethod.BANK_TRANSFER]
        payment_statuses = ['pending', 'completed', 'failed', 'refunded', 'cancelled']
        

        available_bookings = [b for b in bookings if not hasattr(b, 'payment')]
        
        for i in range(min(count, len(available_bookings))):
            booking = random.choice(available_bookings)
            available_bookings.remove(booking)
            
            payment = Payment.objects.create(
                booking=booking,
                user=booking.customer,
                amount=booking.total_price,
                method=random.choice(payment_methods),
                status=random.choice(payment_statuses),
                transaction_id=f"txn_{fake.uuid4()[:8]}" if random.choice([True, False]) else None,
                payment_details={
                    'card_last4': fake.numerify('####') if random.choice([True, False]) else None,
                    'payment_gateway': random.choice(['stripe', 'paypal', 'apple_pay']),
                    'currency': 'EUR'
                }
            )
            
            payments.append(payment)
            
        return payments

    def generate_search_queries(self, count, users):

        search_queries = []
        search_terms = [
            'apartment berlin', 'house munich', 'studio hamburg', 'villa cologne',
            'cheap accommodation', 'luxury apartment', 'pet friendly', 'near center',
            'with parking', 'sea view', 'mountain view', 'city center',
            'family friendly', 'business trip', 'weekend getaway', 'long term rental'
        ]
        
        for i in range(count):
            user = random.choice(users) if random.choice([True, False]) else None
            query = random.choice(search_terms)
            

            existing_query = SearchQuery.objects.filter(query=query, user=user).first()
            if existing_query:
                existing_query.count += 1
                existing_query.save()
                search_queries.append(existing_query)
            else:
                search_query = SearchQuery.objects.create(
                    query=query,
                    user=user,
                    count=random.randint(1, 10)
                )
                search_queries.append(search_query)
                

            SearchHistory.objects.create(
                user=user,
                query=query,
                ip=fake.ipv4() if random.choice([True, False]) else None
            )
            
        return search_queries

    def generate_listing_views(self, count, users, listings):

        listing_views = []
        
        for i in range(count):
            listing = random.choice(listings)
            user = random.choice(users) if random.choice([True, False]) else None
            
            listing_view = ListingView.objects.create(
                listing=listing,
                user=user,
                ip=fake.ipv4() if random.choice([True, False]) else None,
                user_agent=fake.user_agent() if random.choice([True, False]) else None
            )
            
            listing_views.append(listing_view)
            
        return listing_views
