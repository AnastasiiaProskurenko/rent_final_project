import random
import string
import datetime
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.apps import apps
from django.utils import timezone


DEMO_DOMAIN = "demo.local"


def randstr(n=8):
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))


def pick(seq):
    return random.choice(list(seq))


def field_names(model):
    names = set()
    for f in model._meta.get_fields():
        # беремо і python-ім'я поля (name), і DB-ім'я (attname: *_id для FK)
        if hasattr(f, "name"):
            names.add(f.name)
        if hasattr(f, "attname"):
            names.add(f.attname)
    return names



def get_model(label_app, model_name):
    return apps.get_model(label_app, model_name)


def is_required_field(f):
    # Required for DB insert if:
    # - it's a concrete field (not m2m reverse)
    # - not null AND has no default AND not auto-created
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
    # Auto fields
    internal = f.get_internal_type()
    if internal in ("AutoField", "BigAutoField", "SmallAutoField"):
        return False
    return True


def safe_set(obj, name, value):
    if hasattr(obj, name):
        setattr(obj, name, value)


def coerce_default_for_field(f):
    """Generate a safe default value for required NOT NULL fields without defaults."""
    internal = f.get_internal_type()

    # Booleans
    if internal in ("BooleanField",):
        return False

    # Integers
    if internal in ("IntegerField", "BigIntegerField", "SmallIntegerField", "PositiveIntegerField", "PositiveSmallIntegerField"):
        # special realism
        if f.name in ("num_rooms", "rooms"):
            return random.randint(1, 6)
        if f.name in ("num_bedrooms", "bedrooms"):
            return random.randint(0, 4)
        if f.name in ("num_beds", "beds"):
            return random.randint(1, 6)
        if f.name in ("num_bathrooms", "bathrooms"):
            return random.randint(1, 3)
        if f.name in ("num_guests", "guests", "capacity"):
            return random.randint(1, 8)
        if f.name in ("num_nights", "nights"):
            return random.randint(1, 14)
        return random.randint(1, 10)

    # Decimals / floats
    if internal in ("DecimalField",):
        # use field precision if possible
        return Decimal("0.00")
    if internal in ("FloatField",):
        return float(random.randint(1, 10))

    # Dates
    if internal in ("DateField",):
        return timezone.now().date()
    if internal in ("DateTimeField",):
        return timezone.now()

    # Text
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
        if f.name == "address":
            return f"{random.randint(1, 200)} {pick(['Shevchenka', 'Khreshchatyk', 'Bandery', 'Central'])} St"
        if f.name == "description":
            return "Demo description."
        if f.name == "phone":
            return f"+380{random.randint(100000000, 999999999)}"
        if f.name == "status":
            return pick(["active", "inactive", "draft"])
        if f.name == "type":
            return pick(["apartment", "house", "studio"])
        if f.name == "currency":
            return pick(["USD", "EUR", "UAH"])
        if f.name == "image":
            return ""
        if f.name == "photo":
            return ""
        return f"demo_{randstr(12)}"

    # Fallback
    return None


def fill_required_fields(obj):
    """Fill required NOT NULL fields that are still empty."""
    for f in obj._meta.fields:
        if not is_required_field(f):
            continue
        val = getattr(obj, f.name, None)
        if val is not None:
            continue
        generated = coerce_default_for_field(f)
        if generated is not None:
            setattr(obj, f.name, generated)


class Command(BaseCommand):
    help = "Seed demo data for the project (owners, customers, listings, bookings)."

    def add_arguments(self, parser):
        parser.add_argument("--clean", action="store_true", help="Delete existing demo data before seeding")
        parser.add_argument("--owners", type=int, default=3)
        parser.add_argument("--customers", type=int, default=10)
        parser.add_argument("--listings", type=int, default=30)
        parser.add_argument("--bookings", type=int, default=50)
        parser.add_argument("--seed", type=int, default=42)

    @transaction.atomic
    def handle(self, *args, **options):
        random.seed(options["seed"])

        # Models
        User = get_model("users", "User")
        Location = get_model("common", "Location")
        Amenity = get_model("listings", "Amenity")
        Listing = get_model("listings", "Listing")
        ListingPhoto = get_model("listings", "ListingPhoto")
        ListingPrice = get_model("listings", "ListingPrice")
        Booking = get_model("bookings", "Booking")

        # Optional models (create if exist)
        ReviewListingRating = apps.get_model("reviews", "ListingRating") if apps.is_installed("apps.reviews") else None

        if options["clean"]:
            self.stdout.write("Cleaning demo data...")

            # Order matters: children -> parents
            ListingPrice.objects.all().delete()
            self.stdout.write("Deleted listing prices")

            ListingPhoto.objects.all().delete()
            self.stdout.write("Deleted listing photos")

            # Booking depends on listing + user
            Booking.objects.all().delete()
            self.stdout.write("Deleted bookings")

            # Reviews depend on listing/user (optional)
            try:
                if ReviewListingRating:
                    ReviewListingRating.objects.all().delete()
                    self.stdout.write("Deleted listing ratings")
            except Exception:
                pass

            # M2M through table auto cleared with listing delete
            Listing.objects.all().delete()
            self.stdout.write("Deleted listings")

            Amenity.objects.all().delete()
            self.stdout.write("Deleted amenities")

            Location.objects.all().delete()
            self.stdout.write("Deleted locations")

            # Remove demo users
            User.objects.filter(email__endswith=f"@{DEMO_DOMAIN}").delete()
            self.stdout.write("Deleted demo users")

        # ---------- Locations ----------
        self.stdout.write("Creating locations...")
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
        for city, country in cities:
            loc = Location()
            # common patterns: name/city/country/lat/lng
            for nm in ("name", "city"):
                if nm in field_names(Location):
                    safe_set(loc, nm, city)
            if "country" in field_names(Location):
                safe_set(loc, "country", country)
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

        # ---------- Amenities ----------
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
            fill_required_fields(a)
            a.save()
            amenities.append(a)

        # ---------- Users ----------
        def create_demo_user(role_prefix: str, i: int):
            email = f"{role_prefix}{i}@{DEMO_DOMAIN}"
            username = f"{role_prefix}{i}"

            # Create via manager if possible; some custom managers require username
            manager = User.objects
            kwargs = {}
            # USERNAME_FIELD can be email/username; we still pass both if exist.
            if "email" in field_names(User):
                kwargs["email"] = email
            if "username" in field_names(User):
                kwargs["username"] = username

            # If create_user exists, use it; otherwise plain create()
            if hasattr(manager, "create_user"):
                try:
                    user = manager.create_user(password="demo12345", **kwargs)
                except TypeError:
                    # Fallback: create then set_password
                    user = manager.create(**kwargs)
                    user.set_password("demo12345")
                    user.save()
            else:
                user = manager.create(**kwargs)
                if hasattr(user, "set_password"):
                    user.set_password("demo12345")
                    user.save()

            # Optional flags/roles
            for flag in ("is_owner", "is_customer", "is_staff", "is_active"):
                if flag in field_names(User):
                    if flag == "is_active":
                        safe_set(user, flag, True)
                    elif flag == "is_staff":
                        safe_set(user, flag, False)
                    elif flag == "is_owner":
                        safe_set(user, flag, role_prefix.startswith("owner"))
                    elif flag == "is_customer":
                        safe_set(user, flag, role_prefix.startswith("customer"))

            # Names if exist
            if "first_name" in field_names(User):
                safe_set(user, "first_name", pick(["Alex", "Maria", "Ihor", "Olena", "Andrii", "Kateryna"]))
            if "last_name" in field_names(User):
                safe_set(user, "last_name", pick(["Shevchenko", "Koval", "Bondarenko", "Tkachenko", "Melnyk"]))

            fill_required_fields(user)
            user.save()
            return user

        self.stdout.write("Creating owners...")
        owners = [create_demo_user("owner", i + 1) for i in range(options["owners"])]

        self.stdout.write("Creating customers...")
        customers = [create_demo_user("customer", i + 1) for i in range(options["customers"])]

        # ---------- Listings ----------
        self.stdout.write("Creating listings (with photos, amenities, prices)...")

        listing_titles = [
            "Central Apartment", "Cozy Studio", "Modern Loft", "Old Town Flat", "Riverside House",
            "Business Suite", "Family Home", "Minimalist Space", "Panorama View", "Quiet Retreat",
        ]

        listing_objects = []
        for i in range(options["listings"]):
            obj = Listing()

            # Common FK relations
            if "owner" in field_names(Listing):
                safe_set(obj, "owner", pick(owners))
            if "user" in field_names(Listing):
                safe_set(obj, "user", pick(owners))

            # IMPORTANT: location is required (location_id NOT NULL)
            chosen_loc = pick(locations) if locations else None
            if chosen_loc:
                if "location" in field_names(Listing):
                    safe_set(obj, "location", chosen_loc)
                if "location_id" in field_names(Listing):
                    safe_set(obj, "location_id", chosen_loc.id)

            # Common fields
            if "title" in field_names(Listing):
                city = getattr(obj.location, "city", getattr(obj.location, "name", "City")) if getattr(obj, "location", None) else "City"
                safe_set(obj, "title", f"{pick(listing_titles)} in {city} #{i+1}")
            if "description" in field_names(Listing):
                safe_set(obj, "description", "Demo listing with realistic amenities and pricing.")
            if "address" in field_names(Listing):
                safe_set(obj, "address", f"{random.randint(1, 220)} {pick(['Central', 'Green', 'Park', 'River'])} Street")
            if "wifi" in field_names(Listing):
                safe_set(obj, "wifi", random.choice([True, True, False]))
            if "pets_allowed" in field_names(Listing):
                safe_set(obj, "pets_allowed", random.choice([True, False]))
            if "is_active" in field_names(Listing):
                safe_set(obj, "is_active", True)

            # Numeric fields typical for rentals
            if "num_guests" in field_names(Listing):
                safe_set(obj, "num_guests", random.randint(1, 8))
            if "num_bedrooms" in field_names(Listing):
                safe_set(obj, "num_bedrooms", random.randint(0, 4))
            if "num_beds" in field_names(Listing):
                safe_set(obj, "num_beds", random.randint(1, 6))
            if "num_bathrooms" in field_names(Listing):
                safe_set(obj, "num_bathrooms", random.randint(1, 3))

            # IMPORTANT: num_rooms (your current crash)
            if "num_rooms" in field_names(Listing):
                bedrooms = getattr(obj, "num_bedrooms", random.randint(0, 4))
                safe_set(obj, "num_rooms", max(1, int(bedrooms) + random.randint(1, 3)))

            # Pricing if listing has price fields directly
            if "price_per_night" in field_names(Listing):
                safe_set(obj, "price_per_night", Decimal(str(random.randint(25, 250))))
            if "currency" in field_names(Listing):
                safe_set(obj, "currency", pick(["USD", "EUR", "UAH"]))

            # Fill any remaining required NOT NULL fields
            fill_required_fields(obj)
            obj.save()
            listing_objects.append(obj)

            # Attach amenities M2M (if exists)
            if "amenities" in field_names(Listing) and hasattr(obj, "amenities"):
                obj.amenities.set(random.sample(amenities, k=random.randint(3, min(7, len(amenities)))))

            # Create photos
            # Some schemas have fields: listing (FK), url/image, is_cover
            photos_count = random.randint(1, 4)
            for p in range(photos_count):
                ph = ListingPhoto()
                if "listing" in field_names(ListingPhoto):
                    safe_set(ph, "listing", obj)
                if "url" in field_names(ListingPhoto):
                    safe_set(ph, "url", f"https://picsum.photos/seed/{obj.id}-{p}/1200/800")
                if "image" in field_names(ListingPhoto):
                    # keep empty string if image is CharField; if ImageField, leaving None might break
                    safe_set(ph, "image", "")
                if "is_cover" in field_names(ListingPhoto):
                    safe_set(ph, "is_cover", p == 0)
                fill_required_fields(ph)
                ph.save()

            # Create prices (ListingPrice model from your repo)
            # Common fields: listing, start_date, end_date, price_per_night
            base_price = Decimal(str(random.randint(30, 220)))
            # 3 seasonal ranges
            seasons = [
                (timezone.now().date() - datetime.timedelta(days=60), timezone.now().date() + datetime.timedelta(days=30), base_price),
                (timezone.now().date() + datetime.timedelta(days=31), timezone.now().date() + datetime.timedelta(days=120), base_price * Decimal("1.15")),
                (timezone.now().date() + datetime.timedelta(days=121), timezone.now().date() + datetime.timedelta(days=240), base_price * Decimal("0.95")),
            ]
            for sd, ed, pr in seasons:
                lp = ListingPrice()
                if "listing" in field_names(ListingPrice):
                    safe_set(lp, "listing", obj)
                if "start_date" in field_names(ListingPrice):
                    safe_set(lp, "start_date", sd)
                if "end_date" in field_names(ListingPrice):
                    safe_set(lp, "end_date", ed)
                if "price_per_night" in field_names(ListingPrice):
                    safe_set(lp, "price_per_night", pr.quantize(Decimal("0.01")))
                if "currency" in field_names(ListingPrice):
                    safe_set(lp, "currency", pick(["USD", "EUR", "UAH"]))
                fill_required_fields(lp)
                lp.save()

        # ---------- Bookings ----------
        self.stdout.write("Creating bookings...")
        bookings_created = 0
        tries = 0
        max_tries = options["bookings"] * 10

        while bookings_created < options["bookings"] and tries < max_tries:
            tries += 1
            listing = pick(listing_objects)
            customer = pick(customers)

            start = timezone.now().date() + datetime.timedelta(days=random.randint(-20, 60))
            nights = random.randint(1, 10)
            end = start + datetime.timedelta(days=nights)

            b = Booking()
            if "listing" in field_names(Booking):
                safe_set(b, "listing", listing)
            if "customer" in field_names(Booking):
                safe_set(b, "customer", customer)
            if "user" in field_names(Booking):
                safe_set(b, "user", customer)
            if "start_date" in field_names(Booking):
                safe_set(b, "start_date", start)
            if "end_date" in field_names(Booking):
                safe_set(b, "end_date", end)
            if "num_nights" in field_names(Booking):
                safe_set(b, "num_nights", nights)

            # Price fields (your repo changed these recently)
            price = Decimal(str(random.randint(30, 220))).quantize(Decimal("0.01"))
            if "price_per_night" in field_names(Booking):
                safe_set(b, "price_per_night", price)
            if "total_price" in field_names(Booking):
                safe_set(b, "total_price", (price * Decimal(nights)).quantize(Decimal("0.01")))

            # status if exists
            if "status" in field_names(Booking):
                safe_set(b, "status", pick(["pending", "confirmed", "cancelled", "completed"]))

            fill_required_fields(b)

            try:
                b.save()
            except Exception:
                # If collision/validation occurs, skip
                continue

            bookings_created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Seed completed: locations={Location.objects.count()}, amenities={Amenity.objects.count()}, "
            f"owners={len(owners)}, customers={len(customers)}, listings={Listing.objects.count()}, "
            f"bookings={Booking.objects.count()}"
        ))

        self.stdout.write(self.style.WARNING(
            "Demo credentials: any demo user password is demo12345 (emails: owner1@demo.local, customer1@demo.local, ...)"
        ))
