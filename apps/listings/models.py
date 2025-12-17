from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator

from apps.common.models import Location, TimeModel
from apps.common.enums import PropertyType, CancellationPolicy
from apps.common.constants import (
    # Listing info
    LISTING_TITLE_MAX_LENGTH,
    LISTING_DESCRIPTION_MAX_LENGTH,

    # Characteristics
    MIN_ROOMS,
    MAX_ROOMS,
    MIN_BEDROOMS,
    MAX_BEDROOMS,
    MIN_BATHROOMS,
    MAX_BATHROOMS,
    MIN_GUESTS,
    MAX_GUESTS,

    # Area
    AREA_MAX_DIGITS,
    AREA_DECIMAL_PLACES,
    MIN_AREA,
    MAX_AREA,

    # Price
    PRICE_MAX_DIGITS,
    PRICE_DECIMAL_PLACES,
    MIN_PRICE,
    MAX_PRICE,

    # Hotel apartments
    MAX_HOTEL_ROOMS_PER_ADDRESS,
)


class Listing(TimeModel):
    """
    Модель оголошення про нерухомість

    ✅ ВАЛІДАЦІЯ АДРЕСИ:
    1. Звичайна нерухомість (is_hotel_apartment=False):
       - Тільки ОДНЕ оголошення на адресу
       - Тільки ОДИН власник

    2. Квартира готельного типу (is_hotel_apartment=True):
       - Дозволяється ДЕКІЛЬКА оголошень (різні кімнати)
       - Але всі від ОДНОГО власника
       - Максимум MAX_HOTEL_ROOMS_PER_ADDRESS кімнат на адресу
    """

    # ============================================
    # ОСНОВНА ІНФОРМАЦІЯ
    # ============================================

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='listings',
        verbose_name='Owner'
    )

    title = models.CharField(
        max_length=LISTING_TITLE_MAX_LENGTH,  # ✅ Константа
        verbose_name='Title',
        help_text=f'Максимум {LISTING_TITLE_MAX_LENGTH} символів'
    )

    description = models.TextField(
        max_length=LISTING_DESCRIPTION_MAX_LENGTH,  # ✅ Константа
        verbose_name='Description',
        help_text=f'Максимум {LISTING_DESCRIPTION_MAX_LENGTH} символів'
    )

    # ============================================
    # АДРЕСА
    # ============================================

    location = models.ForeignKey(
        Location,
        on_delete=models.PROTECT,
        related_name='listings',
        verbose_name='Location'
    )

    # ✅ Позначка квартири готельного типу
    is_hotel_apartment = models.BooleanField(
        default=False,
        verbose_name='Hotel-type Apartment',
        help_text=(
            'Квартира готельного типу (здаються окремі кімнати). '
            'Якщо True, дозволяється декілька оголошень на одну адресу. '
            f'Максимум {MAX_HOTEL_ROOMS_PER_ADDRESS} кімнат на адресу.'
        )
    )

    # ============================================
    # ХАРАКТЕРИСТИКИ
    # ============================================

    property_type = models.CharField(
        max_length=50,
        choices=PropertyType.choices,
        verbose_name='Property Type'
    )

    num_rooms = models.PositiveIntegerField(
        verbose_name='Number of Rooms',
        validators=[
            MinValueValidator(MIN_ROOMS),  # ✅ Константа
            MaxValueValidator(MAX_ROOMS),  # ✅ Константа
        ],
        help_text=(
            f'Від {MIN_ROOMS} до {MAX_ROOMS} кімнат. '
            'Для hotel apartments - кількість кімнат у цьому оголошенні (що здаються)'
        )
    )

    num_bedrooms = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Number of Bedrooms',
        validators=[
            MinValueValidator(MIN_BEDROOMS),  # ✅ Константа
            MaxValueValidator(MAX_BEDROOMS),  # ✅ Константа
        ],
        help_text=f'Від {MIN_BEDROOMS} до {MAX_BEDROOMS} спалень'
    )

    num_bathrooms = models.PositiveIntegerField(
        default=1,
        verbose_name='Number of Bathrooms',
        validators=[
            MinValueValidator(MIN_BATHROOMS),  # ✅ Константа
            MaxValueValidator(MAX_BATHROOMS),  # ✅ Константа
        ],
        help_text=f'Від {MIN_BATHROOMS} до {MAX_BATHROOMS} ванних кімнат'
    )

    max_guests = models.PositiveIntegerField(
        verbose_name='Maximum Guests',
        validators=[
            MinValueValidator(MIN_GUESTS),  # ✅ Константа
            MaxValueValidator(MAX_GUESTS),  # ✅ Константа
        ],
        help_text=f'Від {MIN_GUESTS} до {MAX_GUESTS} гостей'
    )

    area = models.DecimalField(
        max_digits=AREA_MAX_DIGITS,  # ✅ Константа
        decimal_places=AREA_DECIMAL_PLACES,  # ✅ Константа
        null=True,
        blank=True,
        verbose_name='Area (sq.m.)',
        validators=[
            MinValueValidator(MIN_AREA),  # ✅ Константа
            MaxValueValidator(MAX_AREA),  # ✅ Константа
        ],
        help_text=f'Від {MIN_AREA} до {MAX_AREA} кв.м.'
    )

    # ============================================
    # ЦІНА
    # ============================================

    price = models.DecimalField(
        max_digits=PRICE_MAX_DIGITS,  # ✅ Константа
        decimal_places=PRICE_DECIMAL_PLACES,  # ✅ Константа
        verbose_name='Price per Night',
        validators=[
            MinValueValidator(MIN_PRICE),  # ✅ Константа
            MaxValueValidator(MAX_PRICE),  # ✅ Константа
        ],
        help_text=f'Від {MIN_PRICE} до {MAX_PRICE} за ніч'
    )

    cleaning_fee = models.DecimalField(
        max_digits=PRICE_MAX_DIGITS,  # ✅ Константа
        decimal_places=PRICE_DECIMAL_PLACES,  # ✅ Константа
        null=True,
        blank=True,
        verbose_name='Cleaning Fee',
        help_text='Одноразовий прибиральний збір'
    )

    # ============================================
    # ПОЛІТИКА СКАСУВАННЯ
    # ============================================

    cancellation_policy = models.CharField(
        max_length=20,
        choices=CancellationPolicy.choices,
        default=CancellationPolicy.MODERATE,
        verbose_name='Cancellation Policy'
    )

    # ============================================
    # ЗРУЧНОСТІ
    # ============================================

    amenities = models.ManyToManyField(
        'Amenity',
        related_name='listings',
        blank=True,
        verbose_name='Amenities'
    )

    # ============================================
    # СТАТУС
    # ============================================

    is_active = models.BooleanField(
        default=True,
        verbose_name='Is Active',
        help_text='Чи відображається оголошення на сайті'
    )

    is_verified = models.BooleanField(
        default=False,
        verbose_name='Is Verified',
        help_text='Чи підтверджено оголошення адміністратором'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Listing'
        verbose_name_plural = 'Listings'
        indexes = [
            models.Index(fields=['location']),
            models.Index(fields=['owner', '-created_at']),
            models.Index(fields=['is_active', 'is_verified']),
            models.Index(fields=['price']),
            models.Index(fields=['property_type']),
            models.Index(fields=['is_hotel_apartment']),
        ]

    def __str__(self):
        hotel_mark = " [Hotel Apt]" if self.is_hotel_apartment else ""
        city = self.location.city if self.location else ''
        return f'{self.title} - {city}{hotel_mark}'

    def clean(self):
        """
        Валідація моделі
        ✅ Використовує константи для перевірок
        """
        super().clean()

        if not self.location:
            raise ValidationError({'location': 'Location must be set.'})

        # Валідація унікальності адреси
        self._validate_address_uniqueness()

    def _validate_address_uniqueness(self):
        """
        ✅ КРИТИЧНА ВАЛІДАЦІЯ: Унікальність адреси

        Правила:
        1. Звичайна нерухомість (is_hotel_apartment=False):
           - Тільки ОДНЕ оголошення на адресу
           - Не дозволяємо дублі від будь-кого

        2. Готельна квартира (is_hotel_apartment=True):
           - Дозволяється ДЕКІЛЬКА кімнат
           - Але всі від ОДНОГО власника
           - Максимум MAX_HOTEL_ROOMS_PER_ADDRESS кімнат
        """
        if not self.location:
            return

        # Нормалізуємо адресу для порівняння
        normalized_address = self.location.normalized_address

        # Шукаємо існуючі оголошення на цій адресі
        existing = Listing.objects.filter(
            location__country__iexact=self.location.country,
            location__city__iexact=self.location.city,
        ).exclude(pk=self.pk if self.pk else None)

        # Фільтруємо по нормалізованій адресі
        existing_on_address = existing.filter(
            location__normalized_address=normalized_address
        )

        if not existing_on_address:
            return  # Адреса вільна

        # ============================================
        # ВИПАДОК 1: Створюємо ЗВИЧАЙНУ нерухомість
        # ============================================
        if not self.is_hotel_apartment:
            # Перевіряємо чи є будь-які інші оголошення на цій адресі
            raise ValidationError({
                'address': (
                    f'На адресі "{self.location.address}" вже існує оголошення. '
                    f'Для звичайної нерухомості дозволяється тільки одне оголошення на адресу. '
                    f'Якщо це квартира готельного типу (здаються окремі кімнати), '
                    f'встановіть "Hotel-type Apartment" = True.'
                )
            })

        # ============================================
        # ВИПАДОК 2: Створюємо ГОТЕЛЬНУ КВАРТИРУ
        # ============================================
        if self.is_hotel_apartment:
            # Перевіряємо чи всі існуючі також готельні квартири
            non_hotel = [
                listing for listing in existing_on_address
                if not listing.is_hotel_apartment
            ]

            if non_hotel:
                raise ValidationError({
                    'address': (
                        f'На адресі "{self.location.address}" вже існує звичайне оголошення. '
                        f'Неможливо додати готельну квартиру на цю адресу.'
                    )
                })

            # Перевіряємо чи всі від одного власника
            different_owners = [
                listing for listing in existing_on_address
                if listing.owner != self.owner
            ]

            if different_owners:
                other_owner = different_owners[0].owner
                raise ValidationError({
                    'address': (
                        f'На адресі "{self.location.address}" вже є готельні квартири '
                        f'від іншого власника ({other_owner.get_full_name() or other_owner.email}). '
                        f'Готельні квартири на одній адресі можуть бути тільки від одного власника.'
                    )
                })

            # ✅ Перевіряємо максимальну кількість кімнат
            current_room_count = existing_on_address.count()

            if current_room_count >= MAX_HOTEL_ROOMS_PER_ADDRESS:  # ✅ Константа
                raise ValidationError({
                    'address': (
                        f'Досягнуто максимальну кількість кімнат на одну адресу '
                        f'({MAX_HOTEL_ROOMS_PER_ADDRESS}). '
                        f'Не можна додати більше кімнат на "{self.location.address}".'
                    )
                })

    @staticmethod
    def normalize_address(address: str) -> str:
        """
        Нормалізація адреси для порівняння
        """
        return Location.normalize_address(address)

    @staticmethod
    def count_hotel_rooms_at_location(location: Location, owner) -> int:
        """
        ✅ Підрахунок кількості готельних кімнат на адресі

        Args:
            location: Локація
            owner: Власник

        Returns:
            int: Кількість готельних кімнат
        """
        if not location:
            return 0

        normalized_address = location.normalized_address

        # Знаходимо всі готельні квартири цього власника в місті
        existing = Listing.objects.filter(
            owner=owner,
            location__country__iexact=location.country,
            location__city__iexact=location.city,
            is_hotel_apartment=True
        )

        # Фільтруємо по нормалізованій адресі
        count = existing.filter(
            location__normalized_address=normalized_address
        ).count()

        return count

    @property
    def average_rating(self):
        """Середній рейтинг оголошення"""
        reviews = self.reviews.filter(rating__isnull=False)
        if not reviews.exists():
            return 0
        return reviews.aggregate(models.Avg('rating'))['rating__avg']

    @property
    def review_count(self):
        """Кількість відгуків"""
        return self.reviews.count()

    def get_price_for_nights(self, num_nights: int) -> dict:
        """
        Розрахунок ціни за кількість ночей
        ✅ Використовує константи для обчислень
        """
        from apps.common.constants import PLATFORM_FEE_PERCENTAGE

        base_price = self.price * num_nights
        cleaning_fee = self.cleaning_fee or 0

        subtotal = base_price + cleaning_fee
        platform_fee = subtotal * (PLATFORM_FEE_PERCENTAGE / 100)  # ✅ Константа

        total = subtotal + platform_fee

        return {
            'base_price': float(base_price),
            'nights': num_nights,
            'price_per_night': float(self.price),
            'cleaning_fee': float(cleaning_fee),
            'platform_fee': float(platform_fee),
            'subtotal': float(subtotal),
            'total': float(total),
        }


class Amenity(TimeModel):
    """
    Модель зручностей
    ✅ Використовує константи
    """
    from apps.common.constants import AMENITY_NAME_MAX_LENGTH, AMENITY_ICON_MAX_LENGTH

    name = models.CharField(
        max_length=AMENITY_NAME_MAX_LENGTH,  # ✅ Константа
        unique=True,
        verbose_name='Name'
    )

    icon = models.CharField(
        max_length=AMENITY_ICON_MAX_LENGTH,  # ✅ Константа
        blank=True,
        verbose_name='Icon',
        help_text='Назва іконки (наприклад: wifi, parking, pool)'
    )

    description = models.TextField(
        blank=True,
        verbose_name='Description'
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Amenity'
        verbose_name_plural = 'Amenities'

    def __str__(self):
        return self.name


class ListingPhoto(TimeModel):
    """
    Модель фото оголошення
    """
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name='photos',
        verbose_name='Listing'
    )

    image = models.ImageField(
        upload_to='listings/%Y/%m/%d/',
        verbose_name='Image'
    )

    caption = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Caption'
    )

    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Order',
        help_text='Порядок відображення фото'
    )

    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = 'Listing Photo'
        verbose_name_plural = 'Listing Photos'

    def __str__(self):
        return f'Photo for {self.listing.title}'
