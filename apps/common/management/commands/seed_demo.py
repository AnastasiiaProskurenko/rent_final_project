# apps/common/management/commands/seed_demo_de.py
import random
import datetime
from decimal import Decimal

from django.apps import apps
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone


DEMO_DOMAIN = "demo.local"

# 1x1 PNG (щоб Photo ImageField завжди зберігався)
_PNG_1x1 = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc`\x00\x00"
    b"\x00\x02\x00\x01\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82"
)


def randstr(n: int) -> str:
    alphabet = "abcdefghijklmnopqrstuvwxyz0123456789"
    return "".join(random.choice(alphabet) for _ in range(n))


def pick(seq):
    return random.choice(seq)


def field_names(model):
    return {f.name for f in model._meta.get_fields()}


def is_required_field(f):
    # ManyToMany / reverse rel нас не цікавлять
    if not hasattr(f, "null"):
        return False
    # Auto поля
    if getattr(f, "auto_created", False):
        return False
    # PK / id
    if getattr(f, "primary_key", False):
        return False
    # editable=False часто заповнюється автоматично
    if getattr(f, "editable", True) is False:
        return False
    # null=False і blank=False => required (для form/serializer логіки)
    if getattr(f, "null", True) is False and getattr(f, "blank", True) is False:
        # але якщо default існує — не чіпаємо
        if f.default is not None and f.default is not BaseCommand:
            return False
        return True
    return False


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

        # ✅ ТІЛЬКИ НІМЕЧЧИНА
        if f.name == "city":
            return pick(["Berlin", "Hamburg", "Munich", "Cologne", "Frankfurt am Main", "Stuttgart", "Düsseldorf"])
        if f.name == "country":
            return "Germany"
        if f.name in ("address", "normalized_address"):
            plz = f"{random.randint(10115, 99998):05d}"
            street = pick(["Hauptstraße", "Bahnhofstraße", "Goethestraße", "Schillerstraße", "Mozartstraße", "Poststraße"])
            house = random.randint(1, 250)
            return f"{street} {house}, {plz}"

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
    help = "Seed demo data (Germany only): locations (DE), amenities, users+profiles, listings, bookings, payments, reviews."

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
        UserProfile = apps.get_model("users", "UserProfile")
        Location = apps.get_model("common", "Location")
        Amenity = apps.get_model("listings", "Amenity")
        Listing = apps.get_model("listings", "Listing")
        ListingPhoto = apps.get_model("listings", "ListingPhoto")
        ListingPrice = apps.get_model("listings", "ListingPrice")
        Booking = apps.get_model("bookings", "Booking")
        Payment = apps.get_model("payments", "Payment")
        Review = apps.get_model("reviews", "Review")

        from apps.common.enums import BookingStatus, PaymentStatus, CancellationPolicy, PropertyType, UserRole
        from apps.common.constants import PLATFORM_FEE_PERCENTAGE, MIN_BOOKING_DURATION_DAYS, MAX_BOOKING_DURATION_DAYS

        # ---------- CLEAN ----------
        if opts["clean"]:
            self.stdout.write("Cleaning demo data.")

            Review.objects.all().delete()
            Payment.objects.all().delete()
            Booking.objects.all().delete()
            ListingPhoto.objects.all().delete()
            ListingPrice.objects.all().delete()
            Listing.objects.all().delete()
            Amenity.objects.all().delete()
            Location.objects.all().delete()
            UserProfile.objects.all().delete()
            User.objects.filter(email__endswith=f"@{DEMO_DOMAIN}").delete()

            self.stdout.write("Clean completed.")

        # ---------- LOCATIONS (GERMANY) ----------
        self.stdout.write("Creating DE locations.")

        de_cities = [
            "Berlin", "Hamburg", "Munich", "Cologne", "Frankfurt am Main", "Stuttgart",
            "Düsseldorf", "Dortmund", "Essen", "Leipzig", "Bremen", "Dresden", "Hanover", "Nuremberg",
        ]

        german_streets = [
            "Hauptstraße", "Bahnhofstraße", "Gartenstraße", "Schulstraße", "Ringstraße",
            "Dorfstraße", "Bergstraße", "Lindenstraße", "Berliner Straße", "Goethestraße",
            "Schillerstraße", "Mozartstraße", "Poststraße", "Kirchstraße", "Industriestraße",
        ]

        locations = []
        used_triplets = set()  # (country, city, normalized_address)

        num_locations = max(opts["listings"], 30)

        for _ in range(num_locations):
            city = pick(de_cities)
            country = "Germany"

            plz = f"{random.randint(10115, 99998):05d}"
            street = pick(german_streets)
            house = random.randint(1, 250)

            address = f"{street} {house}, {plz}"
            key = (country.lower(), city.lower(), address.lower())
            while key in used_triplets:
                house = random.randint(1, 250)
                address = f"{street} {house}, {plz}-{randstr(2)}"
                key = (country.lower(), city.lower(), address.lower())
            used_triplets.add(key)

            loc = Location()
            if "country" in field_names(Location):
                safe_set(loc, "country", country)
            if "city" in field_names(Location):
                safe_set(loc, "city", city)
            if "address" in field_names(Location):
                safe_set(loc, "address", address)

            if "normalized_address" in field_names(Location) and not getattr(loc, "normalized_address", None):
                safe_set(loc, "normalized_address", address.lower())

            # Координати в межах Німеччини (приблизно)
            if "latitude" in field_names(Location):
                safe_set(loc, "latitude", Decimal(str(round(random.uniform(47.2, 54.9), 6))))
            if "longitude" in field_names(Location):
                safe_set(loc, "longitude", Decimal(str(round(random.uniform(5.9, 15.1), 6))))
            if "lat" in field_names(Location):
                safe_set(loc, "lat", Decimal(str(round(random.uniform(47.2, 54.9), 6))))
            if "lng" in field_names(Location):
                safe_set(loc, "lng", Decimal(str(round(random.uniform(5.9, 15.1), 6))))

            fill_required_fields(loc)
            loc.save()
            locations.append(loc)

        # ---------- AMENITIES ----------
        self.stdout.write("Creating amenities.")
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

        # ---------- USERS + PROFILES ----------
        def ensure_profile(user, role_value: str):
            """
            Заповнює UserProfile згідно вашої моделі:
            phone, avatar, biography, languages
            """
            profile, _ = UserProfile.objects.get_or_create(user=user)

            # phone (DE)
            if not profile.phone:
                profile.phone = f"+49{random.randint(1500000000, 1799999999)}"

            # languages + biography
            if role_value == UserRole.OWNER:
                profile.languages = "de,en"
                if not profile.biography:
                    profile.biography = (
                        "Property owner in Germany. Experienced host offering clean, well-located apartments."
                    )
            else:
                profile.languages = "de"
                if not profile.biography:
                    profile.biography = (
                        "Guest user. Interested in short-term and long-term rentals in Germany."
                    )

            # avatar
            if not profile.avatar:
                profile.avatar.save(
                    f"avatar_{user.id}.png",
                    ContentFile(_PNG_1x1),
                    save=False
                )

            fill_required_fields(profile)
            profile.save()
            return profile

        def create_demo_user(prefix: str, i: int, role_value: str):
            email = f"{prefix}{i}@{DEMO_DOMAIN}"
            username = f"{prefix}{i}"

            kwargs = {}
            if "email" in field_names(User):
                kwargs["email"] = email
            if "username" in field_names(User):
                kwargs["username"] = username

            manager = User.objects
            if hasattr(manager, "create_user"):
                try:
                    user = manager.create_user(password="demo12345", **kwargs)
                except TypeError:
                    user = manager.create_user(
                        username=kwargs.get("username", username),
                        email=kwargs.get("email", email),
                        password="demo12345"
                    )
            else:
                user = manager.create(**kwargs)
                if hasattr(user, "set_password"):
                    user.set_password("demo12345")
                    user.save()

            if "is_active" in field_names(User):
                safe_set(user, "is_active", True)
            if "is_staff" in field_names(User):
                safe_set(user, "is_staff", False)

            if "first_name" in field_names(User):
                safe_set(user, "first_name", pick(["Max", "Marie", "Leon", "Sophie", "Paul", "Lena"]))
            if "last_name" in field_names(User):
                safe_set(user, "last_name", pick(["Müller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer"]))

            # role + verified (є у вашій моделі User) :contentReference[oaicite:2]{index=2}
            if "role" in field_names(User):
                safe_set(user, "role", role_value)
            if "is_verified" in field_names(User):
                safe_set(user, "is_verified", random.choice([True, False]))

            fill_required_fields(user)
            user.save()

            ensure_profile(user, role_value)
            return user

        self.stdout.write("Creating owners.")
        owners = [create_demo_user("owner", i + 1, UserRole.OWNER) for i in range(opts["owners"])]

        self.stdout.write("Creating customers.")
        customers = [create_demo_user("customer", i + 1, UserRole.CUSTOMER) for i in range(opts["customers"])]

        # ---------- LISTINGS ----------
        self.stdout.write("Creating listings (with photos, amenities, prices).")

        listing_titles = [
            "Central Apartment", "Cozy Studio", "Modern Loft", "Old Town Flat", "Riverside House",
            "Business Suite", "Family Home", "Minimalist Space", "Panorama View", "Quiet Retreat",
        ]

        property_type_values = [c[0] for c in PropertyType.choices]
        cancellation_values = [c[0] for c in CancellationPolicy.choices]

        listing_objects = []
        for i in range(opts["listings"]):
            owner = pick(owners)
            loc = locations[i % len(locations)]

            num_rooms = random.randint(1, 6)
            num_bedrooms = random.randint(0, min(4, num_rooms))
            num_bathrooms = random.randint(1, 3)
            max_guests = random.randint(1, 8)

            area = Decimal(str(random.randint(18, 140))).quantize(Decimal("0.01"))
            price = Decimal(str(random.randint(35, 320))).quantize(Decimal("0.01"))
            cleaning_fee = Decimal(str(random.randint(0, 70))).quantize(Decimal("0.01"))

            obj = Listing(
                owner=owner,
                title=f"{pick(listing_titles)} in {loc.city} #{i+1}",
                description="Demo listing (Germany) with realistic amenities and pricing.",
                location=loc,
                is_hotel_apartment=False,
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

            if hasattr(obj, "amenities"):
                obj.amenities.set(random.sample(amenities, k=random.randint(3, min(7, len(amenities)))))

            ListingPrice.objects.get_or_create(listing=obj, amount=obj.price)

            # Photos: ImageField обязателен -> кладем 1x1 png
            photos_count = random.randint(1, 4)
            for p in range(photos_count):
                ph = ListingPhoto(listing=obj)
                if "caption" in field_names(ListingPhoto):
                    ph.caption = f"Demo photo {p+1}"
                if "order" in field_names(ListingPhoto):
                    ph.order = p
                ph.image.save(
                    f"demo_{obj.id}_{p}.png",
                    ContentFile(_PNG_1x1),
                    save=False
                )
                fill_required_fields(ph)
                ph.save()

        # ---------- BOOKINGS ----------
        self.stdout.write("Creating bookings.")

        today = timezone.now().date()

        total = opts["bookings"]
        completed_count = max(1, total // 5)
        cancelled_count = max(1, total // 5)
        active_count = total - completed_count - cancelled_count

        # 1) COMPLETED (прошлые даты) -> bulk_create, чтобы обойти запрет на прошлое
        completed_bookings = []
        for _ in range(completed_count):
            listing = pick(listing_objects)
            customer = pick(customers)

            nights = random.randint(int(MIN_BOOKING_DURATION_DAYS), min(int(MAX_BOOKING_DURATION_DAYS), 7))
            check_out = today - datetime.timedelta(days=random.randint(1, 25))
            check_in = check_out - datetime.timedelta(days=nights)

            price_entry, _ = ListingPrice.objects.get_or_create(listing=listing, amount=listing.price)

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
            fill_required_fields(b)
            completed_bookings.append(b)

        Booking.objects.bulk_create(completed_bookings)

        # 2) ACTIVE / CANCELLED (будущие даты, обычный save пройдет вашу валидацию)
        all_bookings_db = list(Booking.objects.all())

        bookings_created = 0
        for i in range(active_count + cancelled_count):
            listing = pick(listing_objects)
            customer = pick(customers)

            nights = random.randint(int(MIN_BOOKING_DURATION_DAYS), min(int(MAX_BOOKING_DURATION_DAYS), 7))
            check_in = today + datetime.timedelta(days=random.randint(2, 25))
            check_out = check_in + datetime.timedelta(days=nights)

            b = Booking(
                customer=customer,
                listing=listing,
                location=listing.location,
                check_in=check_in,
                check_out=check_out,
                num_guests=min(listing.max_guests, random.randint(1, 6)),
                cancellation_policy=listing.cancellation_policy,
                special_requests="",
            )

            if i < cancelled_count:
                b.status = BookingStatus.CANCELLED
                b.payment_status = PaymentStatus.FAILED
                if hasattr(b, "cancelled_at"):
                    b.cancelled_at = timezone.now() - datetime.timedelta(days=random.randint(0, 10))
                if hasattr(b, "cancellation_reason"):
                    b.cancellation_reason = "Demo cancellation"
            else:
                b.status = pick([BookingStatus.PENDING, BookingStatus.CONFIRMED])
                b.payment_status = pick([PaymentStatus.PENDING, PaymentStatus.COMPLETED])

            try:
                fill_required_fields(b)
                b.save()
                bookings_created += 1
            except Exception:
                continue

        all_bookings_db = list(Booking.objects.all())
        completed_bookings_db = list(Booking.objects.filter(status=BookingStatus.COMPLETED))

        # ---------- PAYMENTS ----------
        self.stdout.write("Creating payments.")
        for b in all_bookings_db:
            if hasattr(b, "payment"):
                continue

            status = b.payment_status
            status_values = [c[0] for c in PaymentStatus.choices]
            if status not in status_values:
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
            try:
                fill_required_fields(p)
                p.save()
            except Exception:
                continue

        # ---------- REVIEWS ----------
        self.stdout.write("Creating reviews.")
        reviews_created = 0
        review_fields = field_names(Review)

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
                r.save()
                reviews_created += 1
            except Exception:
                continue

        # ---------- DONE ----------
        self.stdout.write(self.style.SUCCESS(
            "Seed (DE) completed: "
            f"locations={Location.objects.count()}, "
            f"amenities={Amenity.objects.count()}, "
            f"owners={len(owners)}, "
            f"customers={len(customers)}, "
            f"profiles={UserProfile.objects.count()}, "
            f"listings={Listing.objects.count()}, "
            f"bookings={Booking.objects.count()}, "
            f"payments={Payment.objects.count()}, "
            f"reviews={reviews_created}"
        ))
        self.stdout.write(self.style.WARNING(
            "Demo credentials: password demo12345 (owner1@demo.local / customer1@demo.local / etc.)"
        ))
