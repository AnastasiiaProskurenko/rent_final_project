from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import Listing, Amenity, ListingPhoto
from apps.reviews.models import OwnerRating
from apps.common.models import Location
from apps.common.constants import (
    # Listing info
    LISTING_TITLE_MIN_LENGTH,
    LISTING_TITLE_MAX_LENGTH,
    LISTING_DESCRIPTION_MIN_LENGTH,
    LISTING_DESCRIPTION_MAX_LENGTH,

    # Photos
    LISTING_PHOTOS_MAX_COUNT,
    LISTING_PHOTO_MAX_SIZE_BYTES,
    LISTING_PHOTO_MAX_SIZE_MB,

    # Characteristics
    MIN_ROOMS,
    MAX_ROOMS,
    MIN_GUESTS,
    MAX_GUESTS,

    # Price
    MIN_PRICE,
    MAX_PRICE,

    # Hotel apartments
    MAX_HOTEL_ROOMS_PER_ADDRESS,

    # Coordinates
    LATITUDE_MAX_DIGITS,
    LATITUDE_DECIMAL_PLACES,
    LONGITUDE_MAX_DIGITS,
    LONGITUDE_DECIMAL_PLACES,
)

User = get_user_model()


class AmenitySerializer(serializers.ModelSerializer):
    """Серіалізатор для зручностей"""

    class Meta:
        model = Amenity
        fields = ('id', 'name', 'icon', 'description')
        read_only_fields = ('id',)


class ListingPhotoSerializer(serializers.ModelSerializer):
    """Серіалізатор для фото оголошень"""

    class Meta:
        model = ListingPhoto
        fields = ('id', 'image', 'caption', 'order', 'created_at')
        read_only_fields = ('id', 'created_at')


class LocationSerializer(serializers.ModelSerializer):
    """Серіалізатор для локації (адреса + координати)"""

    class Meta:
        model = Location
        fields = ('id', 'country', 'city', 'address', 'latitude', 'longitude')
        read_only_fields = ('id',)


class LocationSerializerMixin(serializers.Serializer):
    """
    Міксин для роботи з локацією у серіалізаторах оголошень.
    """

    location = LocationSerializer(read_only=True)
    location_id = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
        help_text='Існуюча локація'
    )
    country = serializers.CharField(write_only=True, required=False)
    city = serializers.CharField(write_only=True, required=False)
    address = serializers.CharField(write_only=True, required=False)
    latitude = serializers.DecimalField(
        max_digits=LATITUDE_MAX_DIGITS,
        decimal_places=LATITUDE_DECIMAL_PLACES,
        required=False,
        allow_null=True
    )
    longitude = serializers.DecimalField(
        max_digits=LONGITUDE_MAX_DIGITS,
        decimal_places=LONGITUDE_DECIMAL_PLACES,
        required=False,
        allow_null=True
    )

    def _update_location_coordinates(self, location: Location, latitude, longitude):
        updated = False
        if latitude is not None and location.latitude != latitude:
            location.latitude = latitude
            updated = True
        if longitude is not None and location.longitude != longitude:
            location.longitude = longitude
            updated = True
        if updated:
            location.save()

    def _create_or_update_location(self, country, city, address, latitude, longitude) -> Location:
        defaults = {}
        if latitude is not None:
            defaults['latitude'] = latitude
        if longitude is not None:
            defaults['longitude'] = longitude

        location, created = Location.objects.get_or_create(
            country=country,
            city=city,
            address=address,
            defaults=defaults
        )

        # Оновлюємо координати, якщо вони змінилися
        self._update_location_coordinates(location, latitude, longitude)
        return location

    def _extract_location(self, attrs: dict) -> Location:
        """
        Повертає або існуючу локацію, або створює нову на основі полів country/city/address.
        """
        location = attrs.pop('location_id', None)
        country = attrs.pop('country', None)
        city = attrs.pop('city', None)
        address = attrs.pop('address', None)
        latitude = attrs.pop('latitude', None)
        longitude = attrs.pop('longitude', None)

        if location:
            self._update_location_coordinates(location, latitude, longitude)
            return location

        if not any([country, city, address]):
            # Використовуємо існуючу локацію, якщо це оновлення
            if getattr(self, 'instance', None) and getattr(self.instance, 'location', None):
                return self.instance.location
            raise serializers.ValidationError({
                'location': 'Location is required.'
            })

        if not all([country, city, address]):
            raise serializers.ValidationError({
                'location': 'Country, city and address are required to set a location.'
            })

        return self._create_or_update_location(
            country.strip(),
            city.strip(),
            address.strip(),
            latitude,
            longitude
        )

    def _inject_location_representation(self, instance, data: dict) -> dict:
        """
        Додає інформацію про локацію у вихідну відповідь.
        """
        if instance.location:
            data['location'] = LocationSerializer(instance.location).data
            data['location_id'] = instance.location.id
            data['country'] = instance.location.country
            data['city'] = instance.location.city
            data['address'] = instance.location.address
            data['latitude'] = instance.location.latitude
            data['longitude'] = instance.location.longitude
        return data


class ListingSerializer(LocationSerializerMixin, serializers.ModelSerializer):
    """
    Повний серіалізатор для оголошень
    ✅ З валідацією унікальності адреси та використанням констант
    """

    # Read-only поля
    owner_name = serializers.SerializerMethodField(read_only=True)
    owner_email = serializers.EmailField(source='owner.email', read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    review_count = serializers.IntegerField(read_only=True)
    owner_rating = serializers.SerializerMethodField(read_only=True)

    # Зручності та фото
    amenities = AmenitySerializer(many=True, read_only=True)
    amenity_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Amenity.objects.all(),
        write_only=True,
        required=False,
        help_text='IDs зручностей'
    )

    photos = ListingPhotoSerializer(many=True, read_only=True)

    # Додаткові поля
    is_hotel_apartment = serializers.BooleanField(
        default=False,
        help_text=(
            'Квартира готельного типу. '
            f'Дозволяє створити до {MAX_HOTEL_ROOMS_PER_ADDRESS} кімнат на одну адресу.'
        )
    )
    hotel_rooms_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Listing
        fields = [
            'id',
            'owner',
            'owner_name',
            'owner_email',

            # Основна інформація
            'title',
            'description',
            'property_type',

            # Адреса
            'location',
            'location_id',
            'country',
            'city',
            'address',
            'latitude',
            'longitude',

            # ✅ Готельна квартира
            'is_hotel_apartment',
            'hotel_rooms_count',

            # Характеристики
            'num_rooms',
            'num_bedrooms',
            'num_bathrooms',
            'max_guests',
            'area',

            # Ціна
            'price',
            'cleaning_fee',
            'cancellation_policy',

            # Зручності
            'amenities',
            'amenity_ids',

            # Фото
            'photos',

            # Рейтинг
            'average_rating',
            'review_count',
            'owner_rating',

            # Статус
            'is_active',
            'is_verified',

            # Системні
            'created_at',
            'updated_at',
        ]
        read_only_fields = (
            'id',
            'owner',
            'average_rating',
            'review_count',
            'owner_rating',
            'is_verified',
            'created_at',
            'updated_at',
        )

    def get_owner_name(self, obj):
        """Отримати ім'я власника"""
        return obj.owner.get_full_name() or obj.owner.email

    def get_owner_rating(self, obj):
        """Отримати агрегований рейтинг власника"""
        try:
            stats = OwnerRating.objects.get(owner=obj.owner)
        except OwnerRating.DoesNotExist:
            return {
                'average_rating': 0.0,
                'total_reviews': 0,
            }

        return {
            'average_rating': float(stats.average_rating),
            'total_reviews': stats.total_reviews,
        }

    def get_hotel_rooms_count(self, obj):
        """
        ✅ Кількість готельних кімнат на адресі
        """
        if not obj.is_hotel_apartment:
            return 0

        return Listing.count_hotel_rooms_at_location(
            location=obj.location,
            owner=obj.owner
        )

    def validate_title(self, value):
        """
        ✅ Валідація заголовку з константами
        """
        value = value.strip()

        if len(value) < LISTING_TITLE_MIN_LENGTH:  # ✅ Константа
            raise serializers.ValidationError(
                f'Title must be at least {LISTING_TITLE_MIN_LENGTH} characters. '
                f'Current length: {len(value)}'
            )

        if len(value) > LISTING_TITLE_MAX_LENGTH:  # ✅ Константа
            raise serializers.ValidationError(
                f'Title cannot exceed {LISTING_TITLE_MAX_LENGTH} characters. '
                f'Current length: {len(value)}'
            )

        return value

    def validate_description(self, value):
        """
        ✅ Валідація опису з константами
        """
        value = value.strip()

        if len(value) < LISTING_DESCRIPTION_MIN_LENGTH:  # ✅ Константа
            raise serializers.ValidationError(
                f'Description must be at least {LISTING_DESCRIPTION_MIN_LENGTH} characters. '
                f'Current length: {len(value)}'
            )

        if len(value) > LISTING_DESCRIPTION_MAX_LENGTH:  # ✅ Константа
            raise serializers.ValidationError(
                f'Description cannot exceed {LISTING_DESCRIPTION_MAX_LENGTH} characters. '
                f'Current length: {len(value)}'
            )

        return value

    def validate_num_rooms(self, value):
        """
        ✅ Валідація кількості кімнат з константами
        """
        if value < MIN_ROOMS or value > MAX_ROOMS:  # ✅ Константи
            raise serializers.ValidationError(
                f'Number of rooms must be between {MIN_ROOMS} and {MAX_ROOMS}. '
                f'Got: {value}'
            )
        return value

    def validate_max_guests(self, value):
        """
        ✅ Валідація кількості гостей з константами
        """
        if value < MIN_GUESTS or value > MAX_GUESTS:  # ✅ Константи
            raise serializers.ValidationError(
                f'Maximum guests must be between {MIN_GUESTS} and {MAX_GUESTS}. '
                f'Got: {value}'
            )
        return value

    def validate_price(self, value):
        """
        ✅ Валідація ціни з константами
        """
        if value < MIN_PRICE or value > MAX_PRICE:  # ✅ Константи
            raise serializers.ValidationError(
                f'Price must be between {MIN_PRICE} and {MAX_PRICE}. '
                f'Got: {value}'
            )
        return value

    def validate(self, attrs):
        """
        ✅ Комплексна валідація з константами
        """
        # Валідація адреси (викликає model.clean())
        # Це перевірить унікальність та готельні квартири

        location = self._extract_location(attrs)
        attrs['location'] = location

        request = self.context.get('request')

        # При створенні - встановлюємо власника
        if not self.instance and request:
            attrs['owner'] = request.user

        is_hotel = attrs.get(
            'is_hotel_apartment',
            self.instance.is_hotel_apartment if self.instance else False
        )

        # Валідація готельних квартир
        if is_hotel:
            # ✅ Перевірка максимальної кількості кімнат
            target_location = location or (self.instance.location if self.instance else None)
            if self.instance:
                # При оновленні
                current_count = Listing.count_hotel_rooms_at_location(
                    location=target_location,
                    owner=self.instance.owner
                )
            else:
                # При створенні
                current_count = Listing.count_hotel_rooms_at_location(
                    location=target_location,
                    owner=attrs['owner']
                )

            if current_count >= MAX_HOTEL_ROOMS_PER_ADDRESS:  # ✅ Константа
                raise serializers.ValidationError({
                    'is_hotel_apartment': (
                        f'Maximum number of hotel rooms ({MAX_HOTEL_ROOMS_PER_ADDRESS}) '
                        f'reached for this address'
                    )
                })

        return attrs

    def create(self, validated_data):
        """Створення оголошення"""
        # Витягуємо amenity_ids
        amenity_ids = validated_data.pop('amenity_ids', [])

        # Створюємо оголошення
        listing = Listing.objects.create(**validated_data)

        # Додаємо зручності
        if amenity_ids:
            listing.amenities.set(amenity_ids)

        return listing

    def update(self, instance, validated_data):
        """Оновлення оголошення"""
        # Витягуємо amenity_ids
        amenity_ids = validated_data.pop('amenity_ids', None)

        # Оновлюємо оголошення
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Оновлюємо зручності
        if amenity_ids is not None:
            instance.amenities.set(amenity_ids)

        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return self._inject_location_representation(instance, data)


class ListingCreateSerializer(LocationSerializerMixin, serializers.ModelSerializer):
    """
    Серіалізатор для створення оголошення
    ✅ З завантаженням фото та використанням констант
    """

    # Поля для завантаження фото
    uploaded_photos = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False,
        help_text=f'Список фото для завантаження (макс {LISTING_PHOTOS_MAX_COUNT})'  # ✅ Константа
    )

    # IDs зручностей
    amenity_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Amenity.objects.all(),
        write_only=True,
        required=False,
        help_text='IDs зручностей'
    )

    class Meta:
        model = Listing
        fields = [
            # Основна інформація
            'title',
            'description',
            'property_type',

            # Адреса
            'location',
            'location_id',
            'country',
            'city',
            'address',
            'latitude',
            'longitude',

            # Готельна квартира
            'is_hotel_apartment',

            # Характеристики
            'num_rooms',
            'num_bedrooms',
            'num_bathrooms',
            'max_guests',
            'area',

            # Ціна
            'price',
            'cleaning_fee',
            'cancellation_policy',

            # Зручності та фото
            'amenity_ids',
            'uploaded_photos',
        ]

    def validate_uploaded_photos(self, value):
        """
        ✅ Валідація завантажених фото з константами
        """
        # ✅ Перевірка кількості
        if len(value) > LISTING_PHOTOS_MAX_COUNT:
            raise serializers.ValidationError(
                f'Maximum {LISTING_PHOTOS_MAX_COUNT} photos allowed. '
                f'Got: {len(value)}'
            )

        # ✅ Перевірка розміру кожного фото
        for photo in value:
            if photo.size > LISTING_PHOTO_MAX_SIZE_BYTES:
                raise serializers.ValidationError(
                    f'Photo "{photo.name}" is too large. '
                    f'Maximum size: {LISTING_PHOTO_MAX_SIZE_MB}MB'
                )

        return value

    def validate(self, attrs):
        location = self._extract_location(attrs)
        attrs['location'] = location

        request = self.context.get('request')
        if not self.instance and request:
            attrs['owner'] = request.user

        if attrs.get('is_hotel_apartment') and attrs.get('owner'):
            current_count = Listing.count_hotel_rooms_at_location(
                location=location,
                owner=attrs['owner']
            )
            if current_count >= MAX_HOTEL_ROOMS_PER_ADDRESS:
                raise serializers.ValidationError({
                    'is_hotel_apartment': (
                        f'Maximum number of hotel rooms ({MAX_HOTEL_ROOMS_PER_ADDRESS}) '
                        f'reached for this address'
                    )
                })

        return attrs

    def create(self, validated_data):
        """Створення оголошення з фото"""
        # Витягуємо фото та amenities
        uploaded_photos = validated_data.pop('uploaded_photos', [])
        amenity_ids = validated_data.pop('amenity_ids', [])

        # Встановлюємо власника
        request = self.context.get('request')
        if request:
            validated_data['owner'] = request.user

        # Створюємо оголошення
        listing = Listing.objects.create(**validated_data)

        # Додаємо зручності
        if amenity_ids:
            listing.amenities.set(amenity_ids)

        # Завантажуємо фото
        for index, photo in enumerate(uploaded_photos):
            ListingPhoto.objects.create(
                listing=listing,
                image=photo,
                order=index
            )

        return listing

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return self._inject_location_representation(instance, data)


class ListingListSerializer(serializers.ModelSerializer):
    """
    ✅ Короткий серіалізатор для списку оголошень:
    тільки назва, ціна, локація, головна фотка, кімнати, макс гостей
    """
    location = LocationSerializer(read_only=True)
    main_photo = serializers.SerializerMethodField()
    owner_name = serializers.SerializerMethodField()

    class Meta:
        model = Listing
        fields = [
            'id',
            'main_photo',
            'owner',
            'owner_name',
            'title',
            'description',
            'property_type',
            'location',
            'max_guests',
            'price',
            'average_rating',
            'is_active',
            'is_verified',
        ]

    def get_main_photo(self, obj):
        """
        У ListingPhoto немає is_main, є order.
        Тому головне фото = перше за order.
        """
        photo = obj.photos.order_by("order", "created_at").first()
        if not photo:
            return None

        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(photo.image.url)
        return photo.image.url

    def get_owner_name(self, obj):
        return obj.owner.get_full_name() or obj.owner.email



class ListingDetailSerializer(ListingSerializer):
    """
    Детальний серіалізатор для окремого оголошення
    ✅ Включає всю інформацію
    """

    # Додаємо інформацію про власника
    owner_info = serializers.SerializerMethodField()

    # Розрахунок ціни
    price_breakdown = serializers.SerializerMethodField()

    class Meta(ListingSerializer.Meta):
        fields = ListingSerializer.Meta.fields + [
            'owner_info',
            'price_breakdown',
        ]

    def get_owner_info(self, obj):
        """Інформація про власника"""
        return {
            'id': obj.owner.id,
            'name': obj.owner.get_full_name() or obj.owner.email,
            'email': obj.owner.email,
            'joined': obj.owner.date_joined,
            'verified': getattr(obj.owner, 'is_verified', False),
            'rating': self.get_owner_rating(obj),
        }

    def get_price_breakdown(self, obj):
        """
        ✅ Розрахунок ціни за різну кількість ночей
        """
        # Приклади для 1, 3, 7 ночей
        return {
            '1_night': obj.get_price_for_nights(1),
            '3_nights': obj.get_price_for_nights(3),
            '7_nights': obj.get_price_for_nights(7),
        }


class PublicListingSerializer(ListingSerializer):
    """Спрощений серіалізатор для неавторизованих користувачів"""

    class Meta(ListingSerializer.Meta):
        fields = [
            'id',
            'owner',
            'owner_name',
            'title',
            'description',
            'property_type',
            'location',
            'country',
            'city',
            'max_guests',
            'price',
            'photos',
            'average_rating',
            'is_active',
            'is_verified',
        ]
        read_only_fields = tuple(fields)


class PublicListingDetailSerializer(PublicListingSerializer):
    """Детальна інформація без даних про власника для гостей"""

    class Meta(PublicListingSerializer.Meta):
        fields = PublicListingSerializer.Meta.fields + [
            'owner_info',
            'price_breakdown',
        ]

    price_breakdown = serializers.SerializerMethodField(read_only=True)
    owner_info = serializers.SerializerMethodField(read_only=True)

    def get_price_breakdown(self, obj):
        return {
            '1_night': obj.get_price_for_nights(1),
            '3_nights': obj.get_price_for_nights(3),
            '7_nights': obj.get_price_for_nights(7),
        }

    def get_owner_info(self, obj):
        return {
            'id': obj.owner.id,
            'name': obj.owner.get_full_name() or obj.owner.email,
            'email': obj.owner.email,
            'joined': obj.owner.date_joined,
            'verified': getattr(obj.owner, 'is_verified', False),
            'rating': self.get_owner_rating(obj),
        }


# ============================================
# ВАЛІДАЦІЯ АДРЕСИ - ДОПОМІЖНІ ФУНКЦІЇ
# ============================================

def validate_listing_address(listing_data: dict, owner, instance=None) -> dict:
    """
    ✅ Валідація адреси оголошення з константами

    Args:
        listing_data: Дані оголошення
        owner: Власник
        instance: Існуюче оголошення (при оновленні)

    Returns:
        dict: Помилки валідації (якщо є)

    Raises:
        serializers.ValidationError: При помилках валідації
    """
    errors = {}

    location = listing_data.get('location')
    is_hotel = listing_data.get('is_hotel_apartment', False)

    if not location:
        country = listing_data.get('country')
        city = listing_data.get('city')
        address = listing_data.get('address')
        if not all([country, city, address]):
            return errors
        location = Location(
            country=country,
            city=city,
            address=address,
            latitude=listing_data.get('latitude'),
            longitude=listing_data.get('longitude'),
            normalized_address=Location.normalize_address(address)
        )

    # Шукаємо існуючі оголошення
    existing_on_address = Listing.objects.filter(
        location__country__iexact=location.country,
        location__city__iexact=location.city,
        location__normalized_address=location.normalized_address,
    ).exclude(pk=instance.pk if instance else None)

    if not existing_on_address.exists():
        return errors  # Адреса вільна

    # Валідація для звичайної нерухомості
    if not is_hotel:
        errors['address'] = (
            f'Address "{location.address}" is already taken. '
            f'For hotel-type apartments, set is_hotel_apartment=True'
        )
        return errors

    # Валідація для готельної квартири
    if is_hotel:
        # Перевірка інших власників
        different_owners = [
            l for l in existing_on_address if l.owner != owner
        ]

        if different_owners:
            errors['address'] = (
                f'Hotel apartments at "{location.address}" belong to different owner. '
                f'All hotel rooms must belong to same owner.'
            )
            return errors

        # ✅ Перевірка максимальної кількості
        if existing_on_address.count() >= MAX_HOTEL_ROOMS_PER_ADDRESS:
            errors['address'] = (
                f'Maximum number of hotel rooms ({MAX_HOTEL_ROOMS_PER_ADDRESS}) '
                f'reached for address "{location.address}"'
            )
            return errors

    return errors
