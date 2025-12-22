from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import models

from .models import Review, ListingRating, OwnerRating
from .serializers import (
    ReviewSerializer,
    ReviewListSerializer,
    ListingRatingSerializer,
    OwnerRatingSerializer,
    OwnerResponseSerializer
)
from .permissions import CanCreateReviewAsCustomer
from apps.listings.models import Listing


class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet для відгуків

    list: Список всіх відгуків користувача
    create: Створити новий відгук
    retrieve: Деталі відгуку
    update/partial_update: Оновити відгук
    destroy: Видалити відгук
    respond: Відповісти на відгук (тільки власник оголошення)
    """

    queryset = Review.objects.select_related(
        'reviewer',
        'listing',
        'booking'
    ).all()
    serializer_class = ReviewSerializer
    permission_classes = [CanCreateReviewAsCustomer]

    def get_queryset(self):
        """
        Фільтрувати відгуки:
        - Всі видимі для анонімних
        - Всі свої для автентифікованих
        """
        queryset = super().get_queryset()

        if self.request.user.is_authenticated:
            # Показати свої відгуки + всі видимі + відгуки на свої оголошення
            return queryset.filter(
                models.Q(reviewer=self.request.user) |
                models.Q(is_visible=True) |
                models.Q(listing__owner=self.request.user)
            )
        else:
            # Тільки видимі для анонімних
            return queryset.filter(is_visible=True)

    def perform_create(self, serializer):
        """Створення відгуку"""
        serializer.save(reviewer=self.request.user)

    def perform_update(self, serializer):
        """Оновлення відгуку - тільки свої"""
        if serializer.instance.reviewer != self.request.user:
            raise permissions.PermissionDenied(
                "You can only edit your own reviews"
            )
        serializer.save()

    def perform_destroy(self, instance):
        """Видалення відгуку - тільки свої"""
        if instance.reviewer != self.request.user:
            raise permissions.PermissionDenied(
                "You can only delete your own reviews"
            )
        instance.delete()

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def respond(self, request, pk=None):
        """
        Відповісти на відгук (тільки власник оголошення)

        POST /api/reviews/{id}/respond/
        {
            "owner_response": "Thank you for your feedback!"
        }
        """
        review = self.get_object()

        # Перевірити що користувач - власник оголошення
        if review.listing.owner != request.user:
            return Response(
                {'detail': 'Only the listing owner can respond to reviews'},
                status=status.HTTP_403_FORBIDDEN
            )

        if review.rating is None:
            return Response(
                {'detail': 'Owner responses are available after a rating has been posted'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Валідувати відповідь
        serializer = OwnerResponseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Оновити відгук
        review.owner_response = serializer.validated_data['owner_response']
        review.owner_response_at = timezone.now()
        review.save()

        return Response(
            ReviewSerializer(review, context={'request': request}).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['delete'], permission_classes=[permissions.IsAuthenticated])
    def remove_response(self, request, pk=None):
        """
        Видалити відповідь власника

        DELETE /api/reviews/{id}/remove_response/
        """
        review = self.get_object()

        # Перевірити що користувач - власник оголошення
        if review.listing.owner != request.user:
            return Response(
                {'detail': 'Only the listing owner can remove responses'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Видалити відповідь
        review.owner_response = ''
        review.owner_response_at = None
        review.save()

        return Response(
            {'detail': 'Response removed successfully'},
            status=status.HTTP_200_OK
        )


class ListingReviewsView(APIView):
    """
    Список відгуків для конкретного оголошення

    GET /api/listings/{listing_id}/reviews/

    Query параметри:
    - rating: фільтр по рейтингу (1-5)
    - sort: сортування (newest, oldest, highest, lowest)
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request, listing_id):
        """Отримати список відгуків"""
        # Перевірити що оголошення існує
        listing = get_object_or_404(Listing, id=listing_id)

        # Отримати відгуки
        reviews = Review.objects.filter(
            listing=listing,
            is_visible=True
        ).select_related('reviewer')

        # Фільтр по рейтингу
        rating_filter = request.query_params.get('rating')
        if rating_filter:
            try:
                rating_filter = int(rating_filter)
                reviews = reviews.filter(rating=rating_filter)
            except ValueError:
                pass

        # Сортування
        sort_param = request.query_params.get('sort', 'newest')
        if sort_param == 'newest':
            reviews = reviews.order_by('-created_at')
        elif sort_param == 'oldest':
            reviews = reviews.order_by('created_at')
        elif sort_param == 'highest':
            reviews = reviews.order_by('-rating', '-created_at')
        elif sort_param == 'lowest':
            reviews = reviews.order_by('rating', '-created_at')
        else:
            reviews = reviews.order_by('-created_at')

        # Серіалізувати
        serializer = ReviewListSerializer(
            reviews,
            many=True,
            context={'request': request}
        )

        return Response({
            'count': reviews.count(),
            'results': serializer.data
        })


class ListingRatingView(APIView):
    """
    Статистика рейтингу оголошення

    GET /api/listings/{listing_id}/rating/
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request, listing_id):
        """Отримати рейтинг оголошення"""
        # Перевірити що оголошення існує
        listing = get_object_or_404(Listing, id=listing_id)

        # Отримати або створити рейтинг
        try:
            rating_stats = ListingRating.objects.get(listing=listing)
        except ListingRating.DoesNotExist:
            # Створити рейтинг якщо не існує
            ListingRating.update_rating(listing_id)
            rating_stats = ListingRating.objects.get(listing=listing)

        # Серіалізувати
        serializer = ListingRatingSerializer(
            rating_stats,
            context={'request': request}
        )

        return Response(serializer.data)


class MyReviewsView(APIView):
    """
    Мої відгуки

    GET /api/reviews/my/
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Отримати всі свої відгуки"""
        reviews = Review.objects.filter(
            reviewer=request.user
        ).select_related('listing', 'booking').order_by('-created_at')

        serializer = ReviewSerializer(
            reviews,
            many=True,
            context={'request': request}
        )

        return Response({
            'count': reviews.count(),
            'results': serializer.data
        })


class TopRatedListingsView(APIView):
    """
    Топ оголошень за рейтингом

    GET /api/listings/top-rated/

    Query параметри:
    - limit: кількість оголошень (default: 10)
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        """Отримати топ оголошень"""
        limit = int(request.query_params.get('limit', 10))

        # Отримати оголошення з найвищим рейтингом
        top_ratings = ListingRating.objects.filter(
            total_reviews__gte=3  # Мінімум 3 відгуки
        ).select_related('listing').order_by(
            '-average_rating',
            '-total_reviews'
        )[:limit]

        serializer = ListingRatingSerializer(
            top_ratings,
            many=True,
            context={'request': request}
        )

        return Response({
            'count': len(serializer.data),
            'results': serializer.data
        })


class OwnerRatingView(APIView):
    """
    Статистика рейтингу власника

    GET /api/owners/{owner_id}/rating/
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request, owner_id):
        """Отримати рейтинг власника"""
        from django.contrib.auth import get_user_model
        User = get_user_model()

        # Перевірити що власник існує
        owner = get_object_or_404(User, id=owner_id)

        # Отримати або створити рейтинг
        try:
            rating_stats = OwnerRating.objects.get(owner=owner)
        except OwnerRating.DoesNotExist:
            # Створити рейтинг якщо не існує
            OwnerRating.update_rating(owner_id)
            try:
                rating_stats = OwnerRating.objects.get(owner=owner)
            except OwnerRating.DoesNotExist:
                # Якщо немає відгуків - повернути порожній рейтинг
                return Response({
                    'owner_id': owner_id,
                    'owner_username': owner.username,
                    'owner_name': f"{owner.first_name} {owner.last_name}".strip() or owner.username,
                    'average_rating': '0.00',
                    'total_reviews': 0,
                    'total_listings': 0,
                    'stars_5': 0,
                    'stars_4': 0,
                    'stars_3': 0,
                    'stars_2': 0,
                    'stars_1': 0,
                    'rating_distribution': {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
                })

        # Серіалізувати
        serializer = OwnerRatingSerializer(
            rating_stats,
            context={'request': request}
        )

        return Response(serializer.data)


class TopRatedOwnersView(APIView):
    """
    Топ власників за рейтингом

    GET /api/owners/top-rated/

    Query параметри:
    - limit: кількість власників (default: 10)
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        """Отримати топ власників"""
        limit = int(request.query_params.get('limit', 10))

        # Отримати власників з найвищим рейтингом
        top_ratings = OwnerRating.objects.filter(
            total_reviews__gte=3  # Мінімум 3 відгуки
        ).select_related('owner').order_by(
            '-average_rating',
            '-total_reviews'
        )[:limit]

        serializer = OwnerRatingSerializer(
            top_ratings,
            many=True,
            context={'request': request}
        )

        return Response({
            'count': len(serializer.data),
            'results': serializer.data
        })


# ════════════════════════════════════════════════════════════════════
# ПРИМІТКИ
# ════════════════════════════════════════════════════════════════════

"""
ENDPOINTS:
──────────────────────────────────────────────────────────────────────

ReviewViewSet:
    GET    /api/reviews/                    - Список своїх відгуків
    POST   /api/reviews/                    - Створити відгук
    GET    /api/reviews/{id}/               - Деталі відгуку
    PATCH  /api/reviews/{id}/               - Оновити відгук
    DELETE /api/reviews/{id}/               - Видалити відгук
    POST   /api/reviews/{id}/respond/       - Відповісти (власник)
    DELETE /api/reviews/{id}/remove_response/ - Видалити відповідь

Listing views:
    GET /api/listings/{id}/reviews/         - Відгуки оголошення
    GET /api/listings/{id}/rating/          - Рейтинг оголошення
    GET /api/listings/top-rated/            - Топ оголошень

Owner views:
    GET /api/owners/{id}/rating/            - Рейтинг власника
    GET /api/owners/top-rated/              - Топ власників

Other:
    GET /api/reviews/my/                    - Мої відгуки
"""
