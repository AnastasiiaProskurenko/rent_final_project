from decimal import Decimal
from datetime import datetime, timedelta

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

from apps.common.models import Location, TimeModel
from apps.common.enums import BookingStatus, PaymentStatus, CancellationPolicy
from apps.common.constants import (
    # Booking constraints
    MIN_BOOKING_DURATION_DAYS,
    MAX_BOOKING_DURATION_DAYS,
    MIN_DAYS_BEFORE_CHECKIN,
    MAX_DAYS_BEFORE_CHECKIN,

    # Guests
    MIN_GUESTS,
    MAX_GUESTS,

    # Special requests
    SPECIAL_REQUESTS_MAX_LENGTH,

    # Price
    PRICE_MAX_DIGITS,
    PRICE_DECIMAL_PLACES,
    MIN_PAYMENT_AMOUNT,

    # Fees
    PLATFORM_FEE_PERCENTAGE,
)
from apps.listings.models import ListingPrice


class Booking(TimeModel):
    """
    Модель бронювання

    ✅ ВАЛІДАЦІЯ:
    1. Дати check-in/check-out коректні
    2. Кількість гостей не перевищує максимум
    3. Немає перетину дат з іншими бронюваннями
    4. Мінімальна/максимальна тривалість
    """

    # ============================================
    # ЗВ'ЯЗКИ
    # ============================================

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name='Customer'
    )

    listing = models.ForeignKey(
        'listings.Listing',
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name='Listing'
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.PROTECT,
        related_name='bookings',
        verbose_name='Location'
    )

    # ============================================
    # ДАТИ
    # ============================================

    check_in = models.DateField(
        verbose_name='Check-in Date'
    )

    check_out = models.DateField(
        verbose_name='Check-out Date'
    )

    # ============================================
    # ГОСТІ
    # ============================================

    num_guests = models.PositiveIntegerField(
        verbose_name='Number of Guests',
        validators=[
            MinValueValidator(MIN_GUESTS),  # ✅ Константа
            MaxValueValidator(MAX_GUESTS),  # ✅ Константа
        ],
        help_text=f'Від {MIN_GUESTS} до {MAX_GUESTS} гостей'
    )

    # ============================================
    # ЦІНА
    # ============================================

    price_per_night = models.ForeignKey(
        'listings.ListingPrice',
        on_delete=models.PROTECT,
        related_name='bookings',
        verbose_name='Price per Night',
        help_text='Ціна на момент бронювання'
    )

    num_nights = models.PositiveIntegerField(
        verbose_name='Number of Nights',
        validators=[
            MinValueValidator(MIN_BOOKING_DURATION_DAYS),  # ✅ Константа
            MaxValueValidator(MAX_BOOKING_DURATION_DAYS),  # ✅ Константа
        ],
        help_text=f'Від {MIN_BOOKING_DURATION_DAYS} до {MAX_BOOKING_DURATION_DAYS} ночей',
        editable=False
    )

    base_price = models.DecimalField(
        max_digits=PRICE_MAX_DIGITS,  # ✅ Константа
        decimal_places=PRICE_DECIMAL_PLACES,  # ✅ Константа
        verbose_name='Base Price',
        help_text='price_per_night * num_nights'
    )

    cleaning_fee = models.DecimalField(
        max_digits=PRICE_MAX_DIGITS,  # ✅ Константа
        decimal_places=PRICE_DECIMAL_PLACES,  # ✅ Константа
        default=0,
        verbose_name='Cleaning Fee'
    )

    platform_fee = models.DecimalField(
        max_digits=PRICE_MAX_DIGITS,  # ✅ Константа
        decimal_places=PRICE_DECIMAL_PLACES,  # ✅ Константа
        verbose_name='Platform Fee',
        help_text=f'{PLATFORM_FEE_PERCENTAGE}% від загальної суми'  # ✅ Константа
    )

    total_price = models.DecimalField(
        max_digits=PRICE_MAX_DIGITS,  # ✅ Константа
        decimal_places=PRICE_DECIMAL_PLACES,  # ✅ Константа
        verbose_name='Total Price',
        validators=[
            MinValueValidator(MIN_PAYMENT_AMOUNT),  # ✅ Константа
        ],
        help_text='Повна вартість бронювання'
    )

    # ============================================
    # СТАТУС
    # ============================================

    status = models.CharField(
        max_length=20,
        choices=BookingStatus.choices,
        default=BookingStatus.PENDING,
        verbose_name='Booking Status'
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        verbose_name='Payment Status'
    )

    # ============================================
    # ДОДАТКОВА ІНФОРМАЦІЯ
    # ============================================

    special_requests = models.TextField(
        max_length=SPECIAL_REQUESTS_MAX_LENGTH,  # ✅ Константа
        blank=True,
        verbose_name='Special Requests',
        help_text=f'Максимум {SPECIAL_REQUESTS_MAX_LENGTH} символів'
    )

    cancellation_policy = models.CharField(
        max_length=20,
        choices=CancellationPolicy.choices,
        verbose_name='Cancellation Policy',
        help_text='Політика скасування на момент бронювання'
    )

    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Cancelled At'
    )

    cancellation_reason = models.TextField(
        blank=True,
        verbose_name='Cancellation Reason'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'
        indexes = [
            models.Index(fields=['customer', '-created_at']),
            models.Index(fields=['listing', 'check_in', 'check_out']),
            models.Index(fields=['location']),
            models.Index(fields=['status']),
            models.Index(fields=['payment_status']),
            models.Index(fields=['check_in', 'check_out']),
        ]

    def __str__(self):
        return (
            f'Booking #{self.pk} - {self.listing.title} '
            f'({self.check_in} to {self.check_out})'
        )

    def clean(self):
        """
        ✅ Валідація бронювання з використанням констант
        """
        super().clean()

        # 1. Валідація дат
        self._validate_dates()

        # 2. Валідація тривалості
        self._validate_duration()

        # 3. Валідація кількості гостей
        self._validate_guests()

        # 4. Валідація перетину дат
        self._validate_date_overlap()

        # 5. Автоматичний розрахунок ціни
        self._calculate_prices()

    def _validate_dates(self):
        """Валідація дат заїзду/виїзду"""
        if not self.check_in or not self.check_out:
            return

        # Check-out має бути після check-in
        if self.check_out <= self.check_in:
            raise ValidationError({
                'check_out': 'Check-out date must be after check-in date'
            })

        # ✅ Використовуємо константи для перевірки максимального часу
        today = timezone.now().date()

        # Мінімальний час до заїзду
        min_checkin = today + timedelta(days=MIN_DAYS_BEFORE_CHECKIN)  # ✅ Константа
        if self.check_in < min_checkin:
            raise ValidationError({
                'check_in': (
                    f'Check-in date must be at least {MIN_DAYS_BEFORE_CHECKIN} days from today'
                )
            })

        # Максимальний час до заїзду
        max_checkin = today + timedelta(days=MAX_DAYS_BEFORE_CHECKIN)  # ✅ Константа
        if self.check_in > max_checkin:
            raise ValidationError({
                'check_in': (
                    f'Check-in date cannot be more than {MAX_DAYS_BEFORE_CHECKIN} days in the future'
                )
            })

    def _validate_duration(self):
        """
        ✅ Валідація тривалості бронювання з константами
        """
        if not self.check_in or not self.check_out:
            return

        duration = (self.check_out - self.check_in).days
        self.num_nights = duration

        # ✅ Мінімальна тривалість
        if duration < MIN_BOOKING_DURATION_DAYS:
            raise ValidationError({
                'check_out': (
                    f'Booking must be at least {MIN_BOOKING_DURATION_DAYS} night(s). '
                    f'Current duration: {duration} night(s)'
                )
            })

        # ✅ Максимальна тривалість
        if duration > MAX_BOOKING_DURATION_DAYS:
            raise ValidationError({
                'check_out': (
                    f'Booking cannot exceed {MAX_BOOKING_DURATION_DAYS} nights. '
                    f'Current duration: {duration} nights'
                )
            })

    def _validate_guests(self):
        """Валідація кількості гостей"""
        if not self.num_guests or not self.listing_id:
            return

        if self.num_guests > self.listing.max_guests:
            raise ValidationError({
                'num_guests': (
                    f'Number of guests ({self.num_guests}) exceeds '
                    f'maximum allowed for this listing ({self.listing.max_guests})'
                )
            })

    def _validate_date_overlap(self):
        """
        ✅ Валідація перетину дат
        Перевіряє чи немає інших підтверджених бронювань на ці дати
        """
        if not all([self.check_in, self.check_out, self.listing_id]):
            return

        # Знаходимо перетинаючі бронювання
        overlapping = Booking.objects.filter(
            listing=self.listing,
            status__in=[
                BookingStatus.PENDING,
                BookingStatus.CONFIRMED,
                BookingStatus.IN_PROGRESS
            ]
        ).exclude(
            pk=self.pk if self.pk else None
        ).filter(
            # Перетин дат
            check_in__lt=self.check_out,
            check_out__gt=self.check_in
        )

        if overlapping.exists():
            conflicting = overlapping.first()
            raise ValidationError({
                'check_in': (
                    f'These dates overlap with another booking '
                    f'({conflicting.check_in} to {conflicting.check_out}). '
                    f'Please choose different dates.'
                )
            })

    def _calculate_prices(self):
        """
        ✅ Автоматичний розрахунок всіх цін з використанням констант
        """
        if not all([self.check_in, self.check_out, self.listing_id]):
            return

        # Кількість ночей
        self.num_nights = (self.check_out - self.check_in).days

        # Ціна за ніч (зберігаємо на момент бронювання з оголошення)
        price_entry, _ = ListingPrice.objects.get_or_create(
            listing=self.listing,
            amount=self.listing.price
        )
        self.price_per_night = price_entry

        # Базова ціна
        cents = Decimal('0.01')
        self.base_price = (self.price_per_night.amount * self.num_nights).quantize(cents)

        # Прибиральний збір
        if not self.cleaning_fee:
            self.cleaning_fee = (self.listing.cleaning_fee or Decimal('0')).quantize(cents)
        else:
            self.cleaning_fee = Decimal(self.cleaning_fee).quantize(cents)

        # Політика скасування
        if not self.cancellation_policy:
            self.cancellation_policy = self.listing.cancellation_policy

        # Підсумок до комісії
        subtotal = (self.base_price + self.cleaning_fee).quantize(cents)

        # ✅ Комісія платформи (використовуємо константу)
        self.platform_fee = (subtotal * (Decimal(PLATFORM_FEE_PERCENTAGE) / Decimal('100'))).quantize(cents)

        # Загальна сума
        self.total_price = (subtotal + self.platform_fee).quantize(cents)

    @property
    def is_cancellable(self) -> bool:
        """
        Чи можна скасувати бронювання
        ✅ Використовує константи для політик скасування
        """
        from apps.common.constants import (
            CANCELLATION_FLEXIBLE_HOURS,
            CANCELLATION_MODERATE_DAYS,
            CANCELLATION_STRICT_DAYS,
            CANCELLATION_SUPER_STRICT_DAYS,
        )

        # Можна скасувати тільки pending або confirmed
        if self.status not in [BookingStatus.PENDING, BookingStatus.CONFIRMED]:
            return False

        now = timezone.now()
        check_in_datetime = timezone.make_aware(
            datetime.combine(self.check_in, datetime.min.time())
        )

        hours_until_checkin = (check_in_datetime - now).total_seconds() / 3600
        days_until_checkin = hours_until_checkin / 24

        # ✅ Використовуємо константи для різних політик
        if self.cancellation_policy == CancellationPolicy.FLEXIBLE:
            return hours_until_checkin >= CANCELLATION_FLEXIBLE_HOURS

        elif self.cancellation_policy == CancellationPolicy.MODERATE:
            return days_until_checkin >= CANCELLATION_MODERATE_DAYS

        elif self.cancellation_policy == CancellationPolicy.STRICT:
            return days_until_checkin >= CANCELLATION_STRICT_DAYS

        elif self.cancellation_policy == CancellationPolicy.SUPER_STRICT:
            return days_until_checkin >= CANCELLATION_SUPER_STRICT_DAYS

        elif self.cancellation_policy == CancellationPolicy.NON_REFUNDABLE:
            return False

        return False

    def calculate_refund_amount(self) -> Decimal:
        """
        ✅ Розрахунок суми повернення з константами
        """
        from apps.common.constants import (
            CANCELLATION_FLEXIBLE_HOURS,
            CANCELLATION_MODERATE_DAYS,
            CANCELLATION_STRICT_DAYS,
            CANCELLATION_SUPER_STRICT_DAYS,
        )

        if not self.is_cancellable:
            return Decimal('0')

        now = timezone.now()
        check_in_datetime = timezone.make_aware(
            datetime.combine(self.check_in, datetime.min.time())
        )

        hours_until_checkin = (check_in_datetime - now).total_seconds() / 3600
        days_until_checkin = hours_until_checkin / 24

        # ✅ Flexible: повне повернення якщо > 24 годин
        if self.cancellation_policy == CancellationPolicy.FLEXIBLE:
            if hours_until_checkin >= CANCELLATION_FLEXIBLE_HOURS:
                return self.total_price
            return Decimal('0')

        # ✅ Moderate: повне якщо > 5 днів
        elif self.cancellation_policy == CancellationPolicy.MODERATE:
            if days_until_checkin >= CANCELLATION_MODERATE_DAYS:
                return self.total_price
            return Decimal('0')

        # ✅ Strict: повне якщо > 7 днів, 50% якщо > 2 днів
        elif self.cancellation_policy == CancellationPolicy.STRICT:
            if days_until_checkin >= CANCELLATION_STRICT_DAYS:
                return self.total_price
            elif days_until_checkin >= 2:
                return self.total_price * Decimal('0.5')
            return Decimal('0')

        # ✅ Super Strict: повне якщо > 30 днів, 50% якщо > 14 днів
        elif self.cancellation_policy == CancellationPolicy.SUPER_STRICT:
            if days_until_checkin >= CANCELLATION_SUPER_STRICT_DAYS:
                return self.total_price
            elif days_until_checkin >= 14:
                return self.total_price * Decimal('0.5')
            return Decimal('0')

        # Non-refundable
        return Decimal('0')

    @property
    def can_review(self) -> bool:
        """Чи можна залишити відгук"""
        return (
                self.status == BookingStatus.COMPLETED and
                self.check_out < timezone.now().date()
        )

    def save(self, *args, **kwargs):
        """Перевизначення save для автоматичних обчислень"""
        # Автоматичний розрахунок перед валідацією
        self._calculate_prices()

        # Валідація перед збереженням
        self.full_clean()
        super().save(*args, **kwargs)
