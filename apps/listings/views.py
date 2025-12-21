from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.search.models import SearchHistory

from .models import Listing, ListingPhoto
from .serializers import (
    ListingSerializer,
    ListingDetailSerializer,
    ListingPhotoSerializer,
    PublicListingSerializer,
    PublicListingDetailSerializer,
)
from .filters import ListingFilter
from .permissions import IsOwnerOrReadOnly


class ListingViewSet(viewsets.ModelViewSet):
    """
    ViewSet для оголошень

    list: Список оголошень
    retrieve: Деталі оголошення
    create: Створити оголошення
    update: Оновити оголошення
    partial_update: Частково оновити оголошення
    destroy: Видалити оголошення
    """

    queryset = Listing.objects.select_related('location', 'owner').all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ListingFilter
    search_fields = ['title', 'description', 'location__city', 'location__address']
    ordering_fields = ['price', 'created_at', 'rating']
    ordering = ['-created_at']

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        search_query = request.query_params.get('search', '').strip()
        filters_data = {
            key: value
            for key, value in request.query_params.items()
            if key not in {'search', 'page', 'page_size', 'ordering'}
            and value not in {'', None}
        }

        if search_query or filters_data:
            SearchHistory.objects.create(
                user=request.user if request.user.is_authenticated else None,
                query=search_query,
                filters=filters_data,
                results_count=queryset.count(),
            )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_serializer_class(self):
        """Використовувати детальний серіалізатор для retrieve"""
        is_authenticated = self.request and self.request.user.is_authenticated

        if self.action == 'retrieve':
            return ListingDetailSerializer if is_authenticated else PublicListingDetailSerializer

        if self.action == 'list':
            return ListingSerializer if is_authenticated else PublicListingSerializer

        return ListingSerializer

    def perform_create(self, serializer):
        """Автоматично встановити власника"""
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Активувати оголошення"""
        listing = self.get_object()
        listing.is_active = True
        listing.save()
        return Response({'status': 'activated'})

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Деактивувати оголошення"""
        listing = self.get_object()
        listing.is_active = False
        listing.save()
        return Response({'status': 'deactivated'})


class ListingPhotoViewSet(viewsets.ModelViewSet):
    """
    ViewSet для фото оголошень

    list: Список фото
    retrieve: Деталі фото
    create: Додати фото
    update: Оновити фото
    destroy: Видалити фото
    """

    queryset = ListingPhoto.objects.all()
    serializer_class = ListingPhotoSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_queryset(self):
        """Фільтрувати фото по оголошенню"""
        queryset = super().get_queryset()
        listing_id = self.request.query_params.get('listing_id')
        if listing_id:
            queryset = queryset.filter(listing_id=listing_id)
        return queryset

    def perform_create(self, serializer):
        """Зберегти фото"""
        serializer.save()

    @action(detail=True, methods=['post'])
    def set_main(self, request, pk=None):
        """Встановити фото як головне"""
        photo = self.get_object()

        # Зняти головне фото з інших фото цього оголошення
        ListingPhoto.objects.filter(
            listing=photo.listing,
            is_main=True
        ).update(is_main=False)

        # Встановити це фото як головне
        photo.is_main = True
        photo.save()

        return Response({'status': 'main photo set'})


# ════════════════════════════════════════════════════════════════════
# ПРИМІТКИ
# ════════════════════════════════════════════════════════════════════

"""
ENDPOINTS:
──────────────────────────────────────────────────────────────────────

ListingViewSet:
    GET    /api/listings/                    - Список оголошень
    POST   /api/listings/                    - Створити оголошення
    GET    /api/listings/{id}/               - Деталі оголошення
    PUT    /api/listings/{id}/               - Оновити оголошення
    PATCH  /api/listings/{id}/               - Частково оновити
    DELETE /api/listings/{id}/               - Видалити оголошення
    POST   /api/listings/{id}/activate/      - Активувати
    POST   /api/listings/{id}/deactivate/    - Деактивувати

ListingPhotoViewSet:
    GET    /api/listing-photos/              - Список фото
    POST   /api/listing-photos/              - Додати фото
    GET    /api/listing-photos/{id}/         - Деталі фото
    PUT    /api/listing-photos/{id}/         - Оновити фото
    DELETE /api/listing-photos/{id}/         - Видалити фото
    POST   /api/listing-photos/{id}/set_main/ - Встановити головним

ФІЛЬТРАЦІЯ:
──────────────────────────────────────────────────────────────────────
GET /api/listings/?listing_type=apartment&city=Kyiv&min_price=100&max_price=500
"""
