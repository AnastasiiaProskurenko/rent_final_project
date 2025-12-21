import base64
import datetime
import random
import string
from decimal import Decimal

from django.apps import apps
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone


DEMO_DOMAIN = "demo.local"


# 1x1 PNG (валидное изображение), чтобы пройти ImageField у ListingPhoto
_PNG_1x1 = base64.b64decode(
    b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGMAAQAABQABDQottAAAAABJRU5ErkJggg=="
)


def randstr(n=8):
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))


def pick(seq):
    return random.choice(list(seq))


def field_names(model):
    names = set()
    for f in model._meta.get_fields():
        if hasattr(f, "name"):
            names.add(f.name)
        if hasattr(f, "attname"):
            names.add(f.attname)
    return names


def is_required_field(f):
    if not getattr(f, "concrete", False):
        return False
    if getattr(f, "auto_created", False):
        return False
    if getattr(f, "primary_key", False):
        return False
    if getattr(f, "many_to_many", False):
        return False
    if getattr(f, "one_to_many", False):
        return False
    if getattr(f, "null", True):
        return False
    if f.has_default():
        return False
    internal = f.get_internal_type()
    if internal in ("AutoField", "BigAutoField", "SmallAutoField"):
        return False
    return True


def coerce_default_for_field(f):
    internal = f.get_internal_type()

    if internal in ("BooleanField",):
        return False

    if internal in (
        "IntegerField", "BigIntegerField", "SmallIntegerField",
        "PositiveIntegerField", "PositiveSmallIntegerField"
    ):
        if f.name in ("num_rooms", "rooms"):
            return random.randint(1, 6)
        if f.name in ("num_bedrooms", "bedrooms"):
            return random.randint(0, 4)
        if f.name in ("num_bathrooms", "bathrooms"):
            return random.randint(1, 3)
        if f.name in ("max_guests", "num_guests", "guests", "capacity"):
            return random.randint(1, 8)
        if f.name in ("order",):
            return 0
        return random.randint(1, 10)

    if internal in ("DecimalField",):
        return Decimal("0.00")

    if internal in ("FloatField",):
        return float(random.randint(1, 10))

    if internal in ("DateField",):
        return timezone.now().date()

    if internal in ("DateTimeField",):
        return timezone.now()

    if internal in ("CharField", "TextField", "SlugField", "EmailField", "URLField"):
        if f.name == "email":
            return f"{randstr(10)}@{DEMO_DOMAIN}"
        if f.name == "username":
            return f"demo_{randstr(10)}"
        if f.name == "title":
            return f"Demo title {randstr(6)}"
        if f.name == "name":
            return f"Demo {randstr(6)}"
        if f.name == "city":
            return pick(["Kyiv", "Lviv", "Odesa", "Kharkiv", "Dnipro", "Warsaw", "Krakow", "Berlin"])
        if f.name == "country":
            return pick(["Ukraine", "Poland", "Germany"])
        if f.name in ("address", "normalized_address"):
            return f"{random.randint(1, 500)} {pick(['Shevchenka', 'Khreshchatyk', 'Bandery', 'Central'])} St {randstr(4)}"
        if f.name == "description":
            return "Demo description."
        if f.name == "status":
            return "pending"
        if f.name == "transaction_id":
            return f"tx_{randstr(16)}"
        return f"demo_{randstr(12)}"

    return None


def fill_required_fields(obj):
    for f in obj._meta.fields:
        if not is_required_field(f):
            continue
        val = getattr(obj, f.name, None)
        if val is not None:
            continue
        generated = coerce_default_for_field(f)
        if generated is not None:
            setattr(obj, f.name, generated)


def safe_set(obj, name, value):
    if hasattr(obj, name):
        setattr(obj, name, value)


class Command(BaseCommand):
    help = "Seed demo data for the project (locations, amenities, users, listings, bookings, payments, reviews)."

    def add_arguments(self, parser):
        parser.add_argument("--clean", action="store_true", help="Delete existing demo data before seeding")
        parser.add_argument("--owners", type=int, default=3)
        parser.add_argument("--customers", type=int, default=10)
        parser.add_argument("--listings", type=int, default=30)
        parser.add_argument("--bookings", type=int, default=50)
        parser.add_argument("--seed", type=int, default=42)

    @transaction.atomic
    def handle(self, *args, **opts):
        random.seed(opts["seed"])

        # Models
        User = apps.get_model("users", "User")
        Location = apps.get_model("common", "Location")
        Amenity = apps.get_model("listings", "Amenity")
        Listing = apps.get_model("listings", "Listing")
        ListingPhoto = apps.get_model("listings", "ListingPhoto")
        ListingPrice = apps.get_model("listings", "ListingPrice")
        Booking = apps.get_model("bookings", "Booking")
        Payment = apps.get_model("payments", "Payment")
        Review = apps.get_model("reviews", "Review")

        from apps.common.enums import BookingStatus, PaymentStatus, CancellationPolicy, PropertyType
        from apps.common.constants import PLATFORM_FEE_PERCENTAGE, MIN_BOOKING_DURATION_DAYS, MAX_BOOKING_DURATION_DAYS

        # ---------- CLEAN ----------
        if opts["clean"]:
            self.stdout.write("Cleaning demo data...")

            # order: children -> parents
            Review.objects.all().delete()
            self.stdout.write("Deleted reviews")

            Payment.objects.all().delete()
            self.stdout.write("Deleted payments")

            Booking.objects.all().delete()
            self.stdout.write("Deleted bookings")

            ListingPhoto.objects.all().delete()
            self.stdout.write("Deleted listing photos")

            ListingPrice.objects.all().delete()
            self.stdout.write("Deleted listing prices")

            Listing.objects.all().delete()
            self.stdout.write("Deleted listings")

            Amenity.objects.all().delete()
            self.stdout.write("Deleted amenities")

            Location.objects.all().delete()
            self.stdout.write("Deleted locations")

            User.objects.filter(email__endswith=f"@{DEMO_DOMAIN}").delete()
            self.stdout.write("Deleted demo users")

        # ---------- LOCATIONS ----------
        self.stdout.write("Creating locations...")

        # ВАЖНО: у вас UNIQUE(country, city, normalized_address)
        # normalized_address формируется из address, поэтому address должен быть уникальным в рамках city+country.
        cities = [
            ("Kyiv", "Ukraine"),
            ("Lviv", "Ukraine"),
            ("Odesa", "Ukraine"),
            ("Kharkiv", "Ukraine"),
            ("Dnipro", "Ukraine"),
            ("Warsaw", "Poland"),
            ("Krakow", "Poland"),
            ("Berlin", "Germany"),
        ]

        locations = []
        used_triplets = set()  # (country, city, normalized_key_like_address)

        # делаем минимум opts["listings"] локаций, чтобы у каждого listing была своя адреса (и не ловить address-валидации listings)
        num_locations = max(opts["listings"], 30)

        for i in range(num_locations):
            city, country = pick(cities)
            # уникальная адреса
            address = f"{random.randint(1, 999)} {pick(['Shevchenka', 'Khreshchatyk', 'Bandery', 'Central', 'Green', 'River'])} St, apt {i+1}-{randstr(3)}"
            key = (country.lower(), city.lower(), address.lower())
            while key in used_triplets:
                address = f"{random.randint(1, 999)} {pick(['Shevchenka', 'Khreshchatyk', 'Bandery', 'Central', 'Green', 'River'])} St, apt {i+1}-{randstr(4)}"
                key = (country.lower(), city.lower(), address.lower())
            used_triplets.add(key)

            loc = Location()
            # обычно есть country/city/address, а normalized_address модель сама посчитает в save()
            if "country" in field_names(Location):
                safe_set(loc, "country", country)
            if "city" in field_names(Location):
                safe_set(loc, "city", city)
            if "address" in field_names(Location):
                safe_set(loc, "address", address)

            # на случай, если normalized_address обязательное и НЕ считается автоматически
            if "normalized_address" in field_names(Location) and not getattr(loc, "normalized_address", None):
                safe_set(loc, "normalized_address", address.lower())

            # координаты если есть
            if "latitude" in field_names(Location):
                safe_set(loc, "latitude", Decimal(str(round(random.uniform(46, 54), 6))))
            if "longitude" in field_names(Location):
                safe_set(loc, "longitude", Decimal(str(round(random.uniform(22, 32), 6))))
            if "lat" in field_names(Location):
                safe_set(loc, "lat", Decimal(str(round(random.uniform(46, 54), 6))))
            if "lng" in field_names(Location):
                safe_set(loc, "lng", Decimal(str(round(random.uniform(22, 32), 6))))

            fill_required_fields(loc)
            loc.save()
            locations.append(loc)

        # ---------- AMENITIES ----------
        self.stdout.write("Creating amenities...")
        amenity_names = [
            "Wi-Fi", "Kitchen", "Air conditioning", "Washer", "Dryer",
            "Heating", "Free parking", "TV", "Elevator", "Balcony",
            "Workspace", "Pet friendly", "Pool", "Gym",
        ]
        amenities = []
        for name in amenity_names:
            a = Amenity()
            if "name" in field_names(Amenity):
                a.name = name
            if "icon" in field_names(Amenity):
                a.icon = randstr(6)
            if "description" in field_names(Amenity):
                a.description = "Demo amenity"
            fill_required_fields(a)
            a.save()
            amenities.append(a)

        # ---------- USERS ----------
        def create_demo_user(prefix: str, i: int):
            email = f"{prefix}{i}@{DEMO_DOMAIN}"
            username = f"{prefix}{i}"

            kwargs = {}
            if "email" in field_names(User):
                kwargs["email"] = email
            if "username" in field_names(User):
                kwargs["username"] = username

            manager = User.objects
            user = None

            if hasattr(manager, "create_user"):
                # у вас create_user требует username (вы это ловили ошибкой)
                try:
                    user = manager.create_user(password="demo12345", **kwargs)
                except TypeError:
                    # если требует строго (username,email,password)
                    user = manager.create_user(username=kwargs.get("username", username), email=kwargs.get("email", email), password="demo12345")
            else:
                user = manager.create(**kwargs)
                if hasattr(user, "set_password"):
                    user.set_password("demo12345")
                    user.save()

            # is_active / is_staff если есть
            if "is_active" in field_names(User):
                safe_set(user, "is_active", True)
            if "is_staff" in field_names(User):
                safe_set(user, "is_staff", False)

            # флаги is_owner/is_customer в вашей модели НЕТ (вы это ловили ошибкой)
            # поэтому не ставим их вообще.

            if "first_name" in field_names(User):
                safe_set(user, "first_name", pick(["Alex", "Maria", "Ihor", "Olena", "Andrii", "Kateryna"]))
            if "last_name" in field_names(User):
                safe_set(user, "last_name", pick(["Shevchenko", "Koval", "Bondarenko", "Tkachenko", "Melnyk"]))

            fill_required_fields(user)
            user.save()
            return user

        self.stdout.write("Creating owners...")
        owners = [create_demo_user("owner", i + 1) for i in range(opts["owners"])]

        self.stdout.write("Creating customers...")
        customers = [create_demo_user("customer", i + 1) for i in range(opts["customers"])]

        # ---------- LISTINGS ----------
        self.stdout.write("Creating listings (with photos, amenities, prices)...")

        listing_titles = [
            "Central Apartment", "Cozy Studio", "Modern Loft", "Old Town Flat", "Riverside House",
            "Business Suite", "Family Home", "Minimalist Space", "Panorama View", "Quiet Retreat",
        ]

        property_type_values = [c[0] for c in PropertyType.choices]  # e.g. ("apartment","house",...)
        cancellation_values = [c[0] for c in CancellationPolicy.choices]

        listing_objects = []
        for i in range(opts["listings"]):
            owner = pick(owners)
            loc = locations[i % len(locations)]  # гарантировано разные адреса

            num_rooms = random.randint(1, 6)
            num_bedrooms = random.randint(0, min(4, num_rooms))
            num_bathrooms = random.randint(1, 3)
            max_guests = random.randint(1, 8)
            area = Decimal(str(random.randint(18, 140))).quantize(Decimal("0.01"))
            price = Decimal(str(random.randint(25, 250))).quantize(Decimal("0.01"))
            cleaning_fee = Decimal(str(random.randint(0, 60))).quantize(Decimal("0.01"))

            obj = Listing(
                owner=owner,
                title=f"{pick(listing_titles)} in {loc.city} #{i+1}",
                description="Demo listing with realistic amenities and pricing.",
                location=loc,
                is_hotel_apartment=False,  # проще: уникальные адреса => не нужно отельное правило
                property_type=pick(property_type_values),
                num_rooms=num_rooms,
                num_bedrooms=num_bedrooms,
                num_bathrooms=num_bathrooms,
                max_guests=max_guests,
                area=area,
                price=price,
                cleaning_fee=cleaning_fee,
                cancellation_policy=pick(cancellation_values),
                is_active=True,
                is_verified=random.choice([True, False]),
            )

            fill_required_fields(obj)
            obj.save()
            listing_objects.append(obj)

            # M2M amenities
            if hasattr(obj, "amenities"):
                obj.amenities.set(random.sample(amenities, k=random.randint(3, min(7, len(amenities)))))

            # ListingPrice: amount == listing.price (и уникален per listing)
            ListingPrice.objects.get_or_create(listing=obj, amount=obj.price)

            # Photos: ImageField обязателен -> кладем 1x1 png
            photos_count = random.randint(1, 4)
            for p in range(photos_count):
                ph = ListingPhoto(listing=obj)
                if "caption" in field_names(ListingPhoto):
                    ph.caption = f"Demo photo {p+1}"
                if "order" in field_names(ListingPhoto):
                    ph.order = p
                # image обязательно
                ph.image.save(
                    f"demo_{obj.id}_{p}.png",
                    ContentFile(_PNG_1x1),
                    save=False
                )
                fill_required_fields(ph)
                ph.save()

        # ---------- BOOKINGS ----------
        self.stdout.write("Creating bookings...")

        today = timezone.now().date()

        # Распределяем статусы
        total = opts["bookings"]
        completed_count = max(1, total // 5)
        cancelled_count = max(1, total // 5)
        active_count = total - completed_count - cancelled_count

        # 1) COMPLETED (прошлые даты) -> bulk_create, чтобы обойти запрет на прошлое
        completed_bookings = []
        for i in range(completed_count):
            listing = pick(listing_objects)
            customer = pick(customers)

            nights = random.randint(int(MIN_BOOKING_DURATION_DAYS), min(int(MAX_BOOKING_DURATION_DAYS), 7))
            # делаем завершение в прошлом
            check_out = today - datetime.timedelta(days=random.randint(1, 25))
            check_in = check_out - datetime.timedelta(days=nights)

            # ListingPrice на момент брони
            price_entry, _ = ListingPrice.objects.get_or_create(listing=listing, amount=listing.price)

            # считаем цены точно по вашей логике (аналог Booking._calculate_prices)
            cents = Decimal("0.01")
            base_price = (price_entry.amount * nights).quantize(cents)
            cleaning_fee_val = (listing.cleaning_fee or Decimal("0")).quantize(cents)
            subtotal = (base_price + cleaning_fee_val).quantize(cents)
            platform_fee = (subtotal * (Decimal(PLATFORM_FEE_PERCENTAGE) / Decimal("100"))).quantize(cents)
            total_price = (subtotal + platform_fee).quantize(cents)

            b = Booking(
                customer=customer,
                listing=listing,
                location=listing.location,
                check_in=check_in,
                check_out=check_out,
                num_guests=min(listing.max_guests, random.randint(1, 6)),
                price_per_night=price_entry,
                num_nights=nights,
                base_price=base_price,
                cleaning_fee=cleaning_fee_val,
                platform_fee=platform_fee,
                total_price=total_price,
                status=BookingStatus.COMPLETED,
                payment_status=PaymentStatus.COMPLETED,
                cancellation_policy=listing.cancellation_policy,
                special_requests="",
            )
            completed_bookings.append(b)

        Booking.objects.bulk_create(completed_bookings)

        # вытаскиваем их обратно с id
        completed_bookings_db = list(
            Booking.objects.filter(status=BookingStatus.COMPLETED).order_by("-id")[:completed_count]
        )

        # 2) CANCELLED (будущие даты) -> обычный save (валидируется)
        cancelled_bookings_db = []
        # чтобы не ловить overlap — двигаем даты последовательно по листингам
        next_start_by_listing = {l.id: today + datetime.timedelta(days=2) for l in listing_objects}

        for _ in range(cancelled_count):
            listing = pick(listing_objects)
            customer = pick(customers)

            start = next_start_by_listing[listing.id]
            nights = random.randint(int(MIN_BOOKING_DURATION_DAYS), min(int(MAX_BOOKING_DURATION_DAYS), 7))
            end = start + datetime.timedelta(days=nights)
            next_start_by_listing[listing.id] = end + datetime.timedelta(days=random.randint(1, 3))

            b = Booking(
                customer=customer,
                listing=listing,
                location=listing.location,
                check_in=start,
                check_out=end,
                num_guests=min(listing.max_guests, random.randint(1, 6)),
                status=BookingStatus.CANCELLED,
                payment_status=pick([PaymentStatus.PENDING, PaymentStatus.FAILED, PaymentStatus.REFUNDED]),
                cancellation_policy=listing.cancellation_policy,
                cancellation_reason="Demo cancellation",
                special_requests="",
            )
            b.save()  # full_clean внутри модели
            if hasattr(b, "cancelled_at"):
                b.cancelled_at = timezone.now() - datetime.timedelta(days=random.randint(0, 7))
                b.save()
            cancelled_bookings_db.append(b)

        # 3) ACTIVE (pending/confirmed/in_progress) -> обычный save (валидируется)
        active_statuses = [BookingStatus.PENDING, BookingStatus.CONFIRMED, BookingStatus.IN_PROGRESS]
        active_bookings_db = []
        for _ in range(active_count):
            listing = pick(listing_objects)
            customer = pick(customers)

            start = next_start_by_listing[listing.id]
            nights = random.randint(int(MIN_BOOKING_DURATION_DAYS), min(int(MAX_BOOKING_DURATION_DAYS), 10))
            end = start + datetime.timedelta(days=nights)
            next_start_by_listing[listing.id] = end + datetime.timedelta(days=random.randint(1, 2))

            status = pick(active_statuses)
            pay_status = pick([PaymentStatus.PENDING, PaymentStatus.COMPLETED])

            b = Booking(
                customer=customer,
                listing=listing,
                location=listing.location,
                check_in=start,
                check_out=end,
                num_guests=min(listing.max_guests, random.randint(1, 6)),
                status=status,
                payment_status=pay_status,
                cancellation_policy=listing.cancellation_policy,
                special_requests=pick(["", "", "Late check-in please", "Need quiet room", "Baby bed if possible"]),
            )
            b.save()
            active_bookings_db.append(b)

        all_bookings_db = completed_bookings_db + cancelled_bookings_db + active_bookings_db

        # ---------- PAYMENTS ----------
        # Payment.clean требует amount == booking.total_price -> ставим ровно booking.total_price
        payments_created = 0
        for b in all_bookings_db:
            # OneToOne: если уже есть — пропускаем
            if hasattr(b, "payment"):
                continue

            status = b.payment_status
            if status not in [c[0] for c in PaymentStatus.choices]:
                status = PaymentStatus.PENDING

            p = Payment(
                booking=b,
                customer=b.customer,
                amount=b.total_price,
                status=status,
                transaction_id=f"tx_{randstr(18)}",
                payment_date=timezone.now() - datetime.timedelta(days=random.randint(0, 30)) if status == PaymentStatus.COMPLETED else None,
                notes="Demo payment",
            )
            p.save()
            payments_created += 1

        # ---------- REVIEWS ----------
        # validate_review_after_stay(booking) требует today >= booking.check_out
        # Поэтому создаем отзывы только для COMPLETED (у них check_out в прошлом).
        self.stdout.write("Creating reviews...")

        reviews_created = 0
        review_fields = field_names(Review)

        # некоторые проекты делают OneToOne(booking) или FK(booking)
        # создадим по 1 review на completed booking
        for b in completed_bookings_db:
            r = Review()

            if "booking" in review_fields:
                safe_set(r, "booking", b)
            if "listing" in review_fields:
                safe_set(r, "listing", b.listing)
            if "customer" in review_fields:
                safe_set(r, "customer", b.customer)
            if "user" in review_fields and "customer" not in review_fields:
                safe_set(r, "user", b.customer)

            if "rating" in review_fields:
                safe_set(r, "rating", random.randint(3, 5))
            if "comment" in review_fields:
                safe_set(r, "comment", pick([
                    "Everything was great, clean and comfortable.",
                    "Nice place, good location. Would stay again.",
                    "Good value for money. Smooth check-in.",
                    "Cozy apartment, friendly host.",
                ]))
            if "is_published" in review_fields:
                safe_set(r, "is_published", True)

            fill_required_fields(r)

            try:
                r.save()  # тут отработает validate_review_after_stay, и он пройдет
                reviews_created += 1
            except Exception:
                # если у Review есть дополнительные строгие правила — просто пропустим
                continue

        # ---------- DONE ----------
        self.stdout.write(self.style.SUCCESS(
            "Seed completed: "
            f"locations={Location.objects.count()}, "
            f"amenities={Amenity.objects.count()}, "
            f"owners={len(owners)}, "
            f"customers={len(customers)}, "
            f"listings={Listing.objects.count()}, "
            f"bookings={Booking.objects.count()}, "
            f"payments={Payment.objects.count()}, "
            f"reviews={Review.objects.count()}"
        ))

        self.stdout.write(self.style.WARNING(
            "Demo credentials: password demo12345 (owner1@demo.local / customer1@demo.local / ...)"
        ))
        self.stdout.write(f"Reviews created: {reviews_created}")
