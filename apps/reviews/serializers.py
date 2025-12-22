from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import Review, ListingRating, OwnerRating
from apps.common.constants import (
    MIN_RATING,
    MAX_RATING,
    REVIEW_COMMENT_MIN_LENGTH,
    REVIEW_COMMENT_MAX_LENGTH,
)

User = get_user_model()


class ReviewerSerializer(serializers.ModelSerializer):
    """Мінімальна інформація про автора відгуку"""

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']
        read_only_fields = ['id', 'username', 'first_name', 'last_name']


class ReviewSerializer(serializers.ModelSerializer):
    """
    Serializer для відгуків

    ✅ Рейтинг 1-5
    ✅ Коментар
    ✅ Відповідь власника
    """

    # Read-only поля
    reviewer = ReviewerSerializer(read_only=True)
    reviewer_name = serializers.CharField(
        source='reviewer.username',
        read_only=True
    )
    listing_title = serializers.CharField(
        source='listing.title',
        read_only=True
    )
    has_owner_response = serializers.BooleanField(read_only=True)

    # Write-only поля
    booking_id = serializers.IntegerField(write_only=True, required=True)

    class Meta:
        model = Review
        fields = [
            # IDs
            'id',
            'booking_id',
            'listing',
            'reviewer',

            # Основна інформація
            'rating',
            'comment',

            # Відповідь власника
            'owner_response',
            'owner_response_at',
            'has_owner_response',

            # Статус
            'is_visible',
            'is_verified',

            # Додаткова інформація
            'reviewer_name',
            'listing_title',

            # Дати
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'listing',
            'reviewer',
            'owner_response',
            'owner_response_at',
            'has_owner_response',
            'reviewer_name',
            'listing_title',
            'is_verified',
            'created_at',
            'updated_at',
        ]

    def validate_rating(self, value):
        """Валідація рейтингу"""
        if value is not None:
            if value < MIN_RATING or value > MAX_RATING:
                raise serializers.ValidationError(
                    f'Rating must be between {MIN_RATING} and {MAX_RATING}'
                )
        return value

    def validate_comment(self, value):
        """Валідація коментаря"""
        if value:
            value = value.strip()

            if len(value) < REVIEW_COMMENT_MIN_LENGTH:
                raise serializers.ValidationError(
                    f'Comment must be at least {REVIEW_COMMENT_MIN_LENGTH} characters'
                )

            if len(value) > REVIEW_COMMENT_MAX_LENGTH:
                raise serializers.ValidationError(
                    f'Comment cannot exceed {REVIEW_COMMENT_MAX_LENGTH} characters'
                )

        return value

    def validate(self, attrs):
        """Загальна валідація"""
        rating = attrs.get('rating')
        comment = attrs.get('comment', '').strip()
        booking_id = attrs.get('booking_id')
        request = self.context.get('request')

        if request and request.user.is_authenticated and request.user.is_owner():
            raise serializers.ValidationError({
                'booking_id': 'Only customers can create reviews'
            })

        # Має бути rating АБО comment
        if not rating and not comment:
            raise serializers.ValidationError(
                'Either rating or comment must be provided'
            )

        # Переконатися, що відгук може залишити лише клієнт
        if booking_id is not None:
            from apps.bookings.models import Booking

            try:
                booking = Booking.objects.select_related('customer', 'listing__owner').get(id=booking_id)
            except Booking.DoesNotExist:
                raise serializers.ValidationError({'booking_id': 'Booking not found'})

            if not request or not request.user.is_authenticated:
                raise serializers.ValidationError({
                    'booking_id': 'Authentication is required to create a review'
                })

            if booking.customer != request.user:
                raise serializers.ValidationError({
                    'booking_id': 'Only the booking customer can leave a review'
                })

            # Зберегти booking для використання під час створення
            attrs['booking_obj'] = booking

        return attrs

    def create(self, validated_data):
        """Створення відгуку"""
        # Отримати booking
        booking = validated_data.pop('booking_obj', None)
        validated_data.pop('booking_id', None)

        if booking is None:
            raise serializers.ValidationError({'booking_id': 'Booking is required to create a review'})

        # Автоматично встановити поля
        validated_data['booking'] = booking
        validated_data['reviewer'] = self.context['request'].user
        validated_data['listing'] = booking.listing

        # Створити відгук (рейтинг оновиться автоматично)
        review = Review.objects.create(**validated_data)

        return review


class ListingRatingSerializer(serializers.ModelSerializer):
    """
    Serializer для статистики рейтингів оголошення

    ✅ Середній рейтинг
    ✅ Кількість відгуків
    ✅ Розподіл за зірками
    """

    listing_id = serializers.IntegerField(source='listing.id', read_only=True)
    listing_title = serializers.CharField(source='listing.title', read_only=True)
    rating_distribution = serializers.ReadOnlyField()

    class Meta:
        model = ListingRating
        fields = [
            # Оголошення
            'listing_id',
            'listing_title',

            # Рейтинг
            'average_rating',
            'total_reviews',

            # Розподіл за зірками
            'stars_5',
            'stars_4',
            'stars_3',
            'stars_2',
            'stars_1',
            'rating_distribution',

            # Дати
            'created_at',
            'updated_at',
        ]
        read_only_fields = '__all__'


class ReviewListSerializer(serializers.ModelSerializer):
    """
    Спрощений serializer для списку відгуків

    Використовується для отримання списку відгуків оголошення
    """

    reviewer_name = serializers.CharField(source='reviewer.username', read_only=True)
    reviewer_avatar = serializers.SerializerMethodField()
    has_owner_response = serializers.BooleanField(read_only=True)

    class Meta:
        model = Review
        fields = [
            'id',
            'reviewer_name',
            'reviewer_avatar',
            'rating',
            'comment',
            'owner_response',
            'has_owner_response',
            'created_at',
        ]
        read_only_fields = '__all__'

    def get_reviewer_avatar(self, obj):
        """Отримати URL аватара (якщо є)"""
        if hasattr(obj.reviewer, 'profile') and obj.reviewer.profile.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.reviewer.profile.avatar.url)
        return None


class OwnerResponseSerializer(serializers.Serializer):
    """
    Serializer для відповіді власника на відгук

    Використовується тільки для оновлення owner_response
    """

    owner_response = serializers.CharField(
        max_length=1000,
        required=True,
        help_text='Відповідь власника на відгук'
    )

    def validate_owner_response(self, value):
        """Валідація відповіді"""
        value = value.strip()

        if len(value) < 10:
            raise serializers.ValidationError(
                'Response must be at least 10 characters'
            )

        if len(value) > 1000:
            raise serializers.ValidationError(
                'Response cannot exceed 1000 characters'
            )

        return value


class OwnerRatingSerializer(serializers.ModelSerializer):
    """
    Serializer для статистики рейтингів власника

    ✅ Середній рейтинг власника
    ✅ Кількість відгуків
    ✅ Кількість оголошень
    ✅ Розподіл за зірками
    """

    owner_id = serializers.IntegerField(source='owner.id', read_only=True)
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    owner_name = serializers.SerializerMethodField()
    rating_distribution = serializers.ReadOnlyField()

    class Meta:
        model = OwnerRating
        fields = [
            # Власник
            'owner_id',
            'owner_username',
            'owner_name',

            # Рейтинг
            'average_rating',
            'total_reviews',
            'total_listings',

            # Розподіл за зірками
            'stars_5',
            'stars_4',
            'stars_3',
            'stars_2',
            'stars_1',
            'rating_distribution',

            # Дати
            'created_at',
            'updated_at',
        ]
        read_only_fields = '__all__'

    def get_owner_name(self, obj):
        """Отримати повне ім'я власника"""
        if obj.owner.first_name or obj.owner.last_name:
            return f"{obj.owner.first_name} {obj.owner.last_name}".strip()
        return obj.owner.username


# ════════════════════════════════════════════════════════════════════
# ПРИМІТКИ
# ════════════════════════════════════════════════════════════════════

"""
ВИКОРИСТАННЯ:
──────────────────────────────────────────────────────────────────────

ReviewSerializer:
    - POST /api/reviews/ - створити відгук
    - GET /api/reviews/{id}/ - отримати відгук
    - PATCH /api/reviews/{id}/ - оновити коментар

ListingRatingSerializer:
    - GET /api/listings/{id}/rating/ - отримати рейтинг оголошення

OwnerRatingSerializer:
    - GET /api/owners/{id}/rating/ - отримати рейтинг власника

ReviewListSerializer:
    - GET /api/listings/{id}/reviews/ - список відгуків оголошення

OwnerResponseSerializer:
    - POST /api/reviews/{id}/respond/ - відповісти на відгук (тільки власник)


ПРИКЛАДИ ЗАПИТІВ:
──────────────────────────────────────────────────────────────────────

# Створити відгук
POST /api/reviews/
{
    "booking_id": 1,
    "rating": 5,
    "comment": "Amazing place! Highly recommended."
}

# Отримати рейтинг оголошення
GET /api/listings/1/rating/
Response:
{
    "listing_id": 1,
    "listing_title": "Beautiful Apartment",
    "average_rating": "4.35",
    "total_reviews": 23,
    "stars_5": 10,
    "stars_4": 8,
    "stars_3": 3,
    "stars_2": 1,
    "stars_1": 1,
    "rating_distribution": {
        "5": 43.5,
        "4": 34.8,
        "3": 13.0,
        "2": 4.3,
        "1": 4.3
    }
}

# Отримати рейтинг власника
GET /api/owners/5/rating/
Response:
{
    "owner_id": 5,
    "owner_username": "john_doe",
    "owner_name": "John Doe",
    "average_rating": "4.65",
    "total_reviews": 47,
    "total_listings": 5,
    "stars_5": 25,
    "stars_4": 15,
    "stars_3": 5,
    "stars_2": 1,
    "stars_1": 1,
    "rating_distribution": {
        "5": 53.2,
        "4": 31.9,
        "3": 10.6,
        "2": 2.1,
        "1": 2.1
    }
}

# Відповісти на відгук (власник)
POST /api/reviews/1/respond/
{
    "owner_response": "Thank you for your kind words! We're glad you enjoyed your stay."
}
"""
