from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import Listing, Amenity, ListingPhoto
from apps.reviews.models import OwnerRating
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


class ListingSerializer(serializers.ModelSerializer):
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

        return Listing.count_hotel_rooms_at_address(
            country=obj.country,
            city=obj.city,
            address=obj.address,
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

        request = self.context.get('request')

        # При створенні - встановлюємо власника
        if not self.instance and request:
            attrs['owner'] = request.user

        # Валідація готельних квартир
        if attrs.get('is_hotel_apartment'):
            # ✅ Перевірка максимальної кількості кімнат
            if self.instance:
                # При оновленні
                current_count = Listing.count_hotel_rooms_at_address(
                    country=attrs.get('country', self.instance.country),
                    city=attrs.get('city', self.instance.city),
                    address=attrs.get('address', self.instance.address),
                    owner=self.instance.owner
                )
            else:
                # При створенні
                current_count = Listing.count_hotel_rooms_at_address(
                    country=attrs['country'],
                    city=attrs['city'],
                    address=attrs['address'],
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


class ListingCreateSerializer(serializers.ModelSerializer):
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


class ListingListSerializer(serializers.ModelSerializer):
    """
    Спрощений серіалізатор для списку оголошень
    ✅ Без детальної інформації, з константами
    """

    owner_name = serializers.SerializerMethodField()
    main_photo = serializers.SerializerMethodField()
    average_rating = serializers.FloatField( read_only=True)
    review_count = serializers.IntegerField( read_only=True)

    class Meta:
        model = Listing
        fields = [
            'id',
            'title',
            'property_type',
            'city',
            'country',
            'price',
            'max_guests',
            'num_rooms',
            'main_photo',
            'average_rating',
            'review_count',
            'owner_name',
            'is_hotel_apartment',
        ]

    def get_owner_name(self, obj):
        """Отримати ім'я власника"""
        return obj.owner.get_full_name() or obj.owner.email

    def get_main_photo(self, obj):
        """Отримати головне фото"""
        photo = obj.photos.first()
        if photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(photo.image.url)
        return None


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
            'title',
            'description',
            'property_type',
            'country',
            'city',
            'address',
            'latitude',
            'longitude',
            'is_hotel_apartment',
            'hotel_rooms_count',
            'num_rooms',
            'num_bedrooms',
            'num_bathrooms',
            'max_guests',
            'area',
            'price',
            'cleaning_fee',
            'cancellation_policy',
            'amenities',
            'amenity_ids',
            'photos',
            'average_rating',
            'review_count',
            'is_active',
            'is_verified',
            'created_at',
            'updated_at',
        ]
        read_only_fields = tuple(fields)


class PublicListingDetailSerializer(PublicListingSerializer):
    """Детальна інформація без даних про власника для гостей"""

    class Meta(PublicListingSerializer.Meta):
        fields = PublicListingSerializer.Meta.fields + [
            'price_breakdown',
        ]

    price_breakdown = serializers.SerializerMethodField(read_only=True)

    def get_price_breakdown(self, obj):
        return {
            '1_night': obj.get_price_for_nights(1),
            '3_nights': obj.get_price_for_nights(3),
            '7_nights': obj.get_price_for_nights(7),
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

    country = listing_data.get('country')
    city = listing_data.get('city')
    address = listing_data.get('address')
    is_hotel = listing_data.get('is_hotel_apartment', False)

    if not all([country, city, address]):
        return errors

    # Нормалізуємо адресу
    normalized = Listing.normalize_address(address)

    # Шукаємо існуючі оголошення
    existing = Listing.objects.filter(
        country__iexact=country,
        city__iexact=city,
    ).exclude(pk=instance.pk if instance else None)

    existing_on_address = [
        listing for listing in existing
        if Listing.normalize_address(listing.address) == normalized
    ]

    if not existing_on_address:
        return errors  # Адреса вільна

    # Валідація для звичайної нерухомості
    if not is_hotel:
        errors['address'] = (
            f'Address "{address}" is already taken. '
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
                f'Hotel apartments at "{address}" belong to different owner. '
                f'All hotel rooms must belong to same owner.'
            )
            return errors

        # ✅ Перевірка максимальної кількості
        if len(existing_on_address) >= MAX_HOTEL_ROOMS_PER_ADDRESS:
            errors['address'] = (
                f'Maximum number of hotel rooms ({MAX_HOTEL_ROOMS_PER_ADDRESS}) '
                f'reached for address "{address}"'
            )
            return errors

    return errors
