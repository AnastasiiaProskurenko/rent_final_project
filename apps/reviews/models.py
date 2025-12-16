from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator

from apps.common.models import TimeModel
from apps.common.enums import BookingStatus
from apps.common.constants import (
    # Rating
    MIN_RATING,
    MAX_RATING,

    # Review text
    REVIEW_COMMENT_MIN_LENGTH,
    REVIEW_COMMENT_MAX_LENGTH,
    OWNER_RESPONSE_MAX_LENGTH,

    # Statistics
    MIN_REVIEWS_FOR_RATING,
    DEFAULT_RATING,
)


class Review(TimeModel):
    """
    Модель відгуку про оголошення

    ✅ ВАЛІДАЦІЯ:
    1. Можна залишити тільки після завершеного бронювання
    2. Один відгук на одне бронювання
    3. rating АБО comment обов'язково (не можна обидва порожні)
    4. Рейтинг від MIN_RATING до MAX_RATING
    """

    # ============================================
    # ЗВ'ЯЗКИ
    # ============================================

    booking = models.OneToOneField(
        'bookings.Booking',
        on_delete=models.CASCADE,
        related_name='review',
        verbose_name='Booking',
        help_text='Бронювання, за яке залишено відгук'
    )

    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews_written',
        verbose_name='Reviewer'
    )

    listing = models.ForeignKey(
        'listings.Listing',
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Listing'
    )

    # ============================================
    # РЕЙТИНГ 1-5
    # ============================================

    rating = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Overall Rating',
        validators=[
            MinValueValidator(MIN_RATING),
            MaxValueValidator(MAX_RATING),
        ],
        help_text=f'Загальний рейтинг від {MIN_RATING} до {MAX_RATING} зірок'
    )

    # ============================================
    # КОМЕНТАР
    # ============================================

    comment = models.TextField(
        max_length=REVIEW_COMMENT_MAX_LENGTH,
        blank=True,
        verbose_name='Comment',
        help_text=(
            f'Текстовий відгук (мінімум {REVIEW_COMMENT_MIN_LENGTH}, '
            f'максимум {REVIEW_COMMENT_MAX_LENGTH} символів)'
        )
    )

    # ============================================
    # ВІДПОВІДЬ ВЛАСНИКА
    # ============================================

    owner_response = models.TextField(
        max_length=OWNER_RESPONSE_MAX_LENGTH,
        blank=True,
        verbose_name='Owner Response',
        help_text=f'Відповідь власника (максимум {OWNER_RESPONSE_MAX_LENGTH} символів)'
    )

    owner_response_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Owner Response Date'
    )

    # ============================================
    # СТАТУС
    # ============================================

    is_visible = models.BooleanField(
        default=True,
        verbose_name='Is Visible',
        help_text='Чи відображається відгук на сайті'
    )

    is_verified = models.BooleanField(
        default=True,
        verbose_name='Is Verified',
        help_text='Підтверджений відгук (від реального гостя)'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        indexes = [
            models.Index(fields=['listing', '-created_at']),
            models.Index(fields=['reviewer', '-created_at']),
            models.Index(fields=['rating']),
            models.Index(fields=['is_visible', '-created_at']),
        ]

    def __str__(self):
        rating_text = f'{self.rating}★' if self.rating else 'No rating'
        return f'Review by {self.reviewer} - {rating_text}'

    def clean(self):
        """Валідація відгуку"""
        super().clean()

        # 1. Критична валідація: rating АБО comment
        self._validate_rating_or_comment()

        # 2. Валідація довжини коментаря
        self._validate_comment_length()

        # 3. Валідація бронювання
        self._validate_booking()

        # 4. Валідація дублювання
        self._validate_duplicate()

    def _validate_rating_or_comment(self):
        """✅ КРИТИЧНА ВАЛІДАЦІЯ: Має бути rating АБО comment"""
        has_rating = self.rating is not None
        has_comment = bool(self.comment and self.comment.strip())

        if not has_rating and not has_comment:
            raise ValidationError(
                'Either rating or comment must be provided. Both cannot be empty.'
            )

    def _validate_comment_length(self):
        """Валідація довжини коментаря"""
        if self.comment:
            comment = self.comment.strip()

            if len(comment) < REVIEW_COMMENT_MIN_LENGTH:
                raise ValidationError({
                    'comment': (
                        f'Comment must be at least {REVIEW_COMMENT_MIN_LENGTH} characters. '
                        f'Current length: {len(comment)}'
                    )
                })

            if len(comment) > REVIEW_COMMENT_MAX_LENGTH:
                raise ValidationError({
                    'comment': (
                        f'Comment cannot exceed {REVIEW_COMMENT_MAX_LENGTH} characters. '
                        f'Current length: {len(comment)}'
                    )
                })

    def _validate_booking(self):
        """Валідація бронювання"""
        if not self.booking_id:
            return

        # Перевірка що бронювання завершене
        if self.booking.status != BookingStatus.COMPLETED:
            raise ValidationError({
                'booking': 'Can only review completed bookings'
            })

        # Автоматично заповнюємо поля
        if not self.reviewer_id:
            self.reviewer = self.booking.customer

        if not self.listing_id:
            self.listing = self.booking.listing

    def _validate_duplicate(self):
        """Валідація дублювання відгуків"""
        if not self.booking_id:
            return

        existing = Review.objects.filter(
            booking=self.booking
        ).exclude(pk=self.pk if self.pk else None)

        if existing.exists():
            raise ValidationError({
                'booking': 'Review for this booking already exists'
            })

    @property
    def has_owner_response(self) -> bool:
        """Чи є відповідь власника"""
        return bool(self.owner_response and self.owner_response.strip())

    def save(self, *args, **kwargs):
        """Перевизначення save для автоматичних обчислень"""
        if not self.pk:
            self.full_clean()

        super().save(*args, **kwargs)

        # ✅ Оновити рейтинг оголошення після збереження відгуку
        self._update_listing_rating()

        # ✅ Оновити рейтинг власника після збереження відгуку
        self._update_owner_rating()

    def _update_listing_rating(self):
        """Оновити агрегований рейтинг оголошення"""
        if self.listing_id:
            ListingRating.update_rating(self.listing_id)

    def _update_owner_rating(self):
        """Оновити агрегований рейтинг власника"""
        if self.listing_id and self.listing.owner_id:
            OwnerRating.update_rating(self.listing.owner_id)


class ListingRating(TimeModel):
    """
    ✅ Агрегований рейтинг оголошення

    Зберігає середній рейтинг та кількість відгуків для швидкого доступу
    Оновлюється автоматично при додаванні/видаленні відгуків
    """

    listing = models.OneToOneField(
        'listings.Listing',
        on_delete=models.CASCADE,
        related_name='rating_stats',
        verbose_name='Listing',
        primary_key=True
    )

    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0,
        verbose_name='Average Rating',
        help_text='Середній рейтинг (0.00 - 5.00)'
    )

    total_reviews = models.PositiveIntegerField(
        default=0,
        verbose_name='Total Reviews',
        help_text='Загальна кількість відгуків'
    )

    # Розподіл за зірками
    stars_5 = models.PositiveIntegerField(default=0, verbose_name='5 Stars')
    stars_4 = models.PositiveIntegerField(default=0, verbose_name='4 Stars')
    stars_3 = models.PositiveIntegerField(default=0, verbose_name='3 Stars')
    stars_2 = models.PositiveIntegerField(default=0, verbose_name='2 Stars')
    stars_1 = models.PositiveIntegerField(default=0, verbose_name='1 Star')

    class Meta:
        verbose_name = 'Listing Rating'
        verbose_name_plural = 'Listing Ratings'

    def __str__(self):
        return f'{self.listing.title} - {self.average_rating}★ ({self.total_reviews} reviews)'

    @classmethod
    def update_rating(cls, listing_id):
        """
        Оновити рейтинг оголошення

        Args:
            listing_id: ID оголошення
        """
        # Отримати всі видимі відгуки з рейтингом
        reviews = Review.objects.filter(
            listing_id=listing_id,
            is_visible=True,
            rating__isnull=False
        )

        total_reviews = reviews.count()

        if total_reviews == 0:
            # Немає відгуків - скидаємо рейтинг
            cls.objects.update_or_create(
                listing_id=listing_id,
                defaults={
                    'average_rating': 0,
                    'total_reviews': 0,
                    'stars_5': 0,
                    'stars_4': 0,
                    'stars_3': 0,
                    'stars_2': 0,
                    'stars_1': 0,
                }
            )
            return

        # Обчислити середній рейтинг
        ratings = reviews.values_list('rating', flat=True)
        average_rating = sum(ratings) / len(ratings)

        # Підрахувати розподіл за зірками
        stars_count = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for rating in ratings:
            stars_count[rating] += 1

        # Оновити або створити запис
        cls.objects.update_or_create(
            listing_id=listing_id,
            defaults={
                'average_rating': round(average_rating, 2),
                'total_reviews': total_reviews,
                'stars_5': stars_count[5],
                'stars_4': stars_count[4],
                'stars_3': stars_count[3],
                'stars_2': stars_count[2],
                'stars_1': stars_count[1],
            }
        )

    @property
    def rating_distribution(self) -> dict:
        """
        Отримати розподіл рейтингів у відсотках

        Returns:
            dict: Словник з відсотками для кожної зірки
        """
        if self.total_reviews == 0:
            return {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}

        return {
            5: round((self.stars_5 / self.total_reviews) * 100, 1),
            4: round((self.stars_4 / self.total_reviews) * 100, 1),
            3: round((self.stars_3 / self.total_reviews) * 100, 1),
            2: round((self.stars_2 / self.total_reviews) * 100, 1),
            1: round((self.stars_1 / self.total_reviews) * 100, 1),
        }


class OwnerRating(TimeModel):
    """
    ✅ Агрегований рейтинг власника оголошень

    Зберігає середній рейтинг всіх оголошень власника
    Оновлюється автоматично при додаванні/видаленні відгуків
    """

    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owner_rating_stats',
        verbose_name='Owner',
        primary_key=True
    )

    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0,
        verbose_name='Average Rating',
        help_text='Середній рейтинг власника (0.00 - 5.00)'
    )

    total_reviews = models.PositiveIntegerField(
        default=0,
        verbose_name='Total Reviews',
        help_text='Загальна кількість відгуків на всі оголошення'
    )

    total_listings = models.PositiveIntegerField(
        default=0,
        verbose_name='Total Listings',
        help_text='Кількість оголошень з відгуками'
    )

    # Розподіл за зірками
    stars_5 = models.PositiveIntegerField(default=0, verbose_name='5 Stars')
    stars_4 = models.PositiveIntegerField(default=0, verbose_name='4 Stars')
    stars_3 = models.PositiveIntegerField(default=0, verbose_name='3 Stars')
    stars_2 = models.PositiveIntegerField(default=0, verbose_name='2 Stars')
    stars_1 = models.PositiveIntegerField(default=0, verbose_name='1 Star')

    class Meta:
        verbose_name = 'Owner Rating'
        verbose_name_plural = 'Owner Ratings'

    def __str__(self):
        return f'{self.owner.username} - {self.average_rating}★ ({self.total_reviews} reviews)'

    @classmethod
    def update_rating(cls, owner_id):
        """
        Оновити рейтинг власника

        Args:
            owner_id: ID власника (User)
        """
        from apps.listings.models import Listing

        # Отримати всі оголошення власника
        owner_listings = Listing.objects.filter(owner_id=owner_id)

        # Отримати всі видимі відгуки на оголошення власника
        reviews = Review.objects.filter(
            listing__in=owner_listings,
            is_visible=True,
            rating__isnull=False
        )

        total_reviews = reviews.count()

        if total_reviews == 0:
            # Немає відгуків - скидаємо рейтинг
            cls.objects.update_or_create(
                owner_id=owner_id,
                defaults={
                    'average_rating': 0,
                    'total_reviews': 0,
                    'total_listings': 0,
                    'stars_5': 0,
                    'stars_4': 0,
                    'stars_3': 0,
                    'stars_2': 0,
                    'stars_1': 0,
                }
            )
            return

        # Обчислити середній рейтинг
        ratings = reviews.values_list('rating', flat=True)
        average_rating = sum(ratings) / len(ratings)

        # Підрахувати розподіл за зірками
        stars_count = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for rating in ratings:
            stars_count[rating] += 1

        # Кількість оголошень з відгуками
        listings_with_reviews = reviews.values('listing').distinct().count()

        # Оновити або створити запис
        cls.objects.update_or_create(
            owner_id=owner_id,
            defaults={
                'average_rating': round(average_rating, 2),
                'total_reviews': total_reviews,
                'total_listings': listings_with_reviews,
                'stars_5': stars_count[5],
                'stars_4': stars_count[4],
                'stars_3': stars_count[3],
                'stars_2': stars_count[2],
                'stars_1': stars_count[1],
            }
        )

    @property
    def rating_distribution(self) -> dict:
        """
        Отримати розподіл рейтингів у відсотках

        Returns:
            dict: Словник з відсотками для кожної зірки
        """
        if self.total_reviews == 0:
            return {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}

        return {
            5: round((self.stars_5 / self.total_reviews) * 100, 1),
            4: round((self.stars_4 / self.total_reviews) * 100, 1),
            3: round((self.stars_3 / self.total_reviews) * 100, 1),
            2: round((self.stars_2 / self.total_reviews) * 100, 1),
            1: round((self.stars_1 / self.total_reviews) * 100, 1),
        }


# ════════════════════════════════════════════════════════════════════
# ПРИМІТКИ
# ════════════════════════════════════════════════════════════════════

"""
✅ Review:
   - Відгук про оголошення
   - Рейтинг 1-5 + коментар
   - Автоматично оновлює ListingRating і OwnerRating

✅ ListingRating:
   - Агрегований рейтинг оголошення
   - Середній рейтинг + кількість відгуків
   - Розподіл за зірками

✅ OwnerRating:
   - Агрегований рейтинг власника
   - Середній рейтинг по всіх оголошеннях
   - Розподіл за зірками
   - Кількість оголошень з відгуками
"""
