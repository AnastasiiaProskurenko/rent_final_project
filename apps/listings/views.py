from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Listing, ListingPhoto
from .serializers import (
    ListingSerializer,
    ListingDetailSerializer,
    ListingPhotoSerializer,
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

    queryset = Listing.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ListingFilter
    search_fields = ['title', 'description', 'city']
    ordering_fields = ['price', 'created_at', 'rating']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Використовувати детальний серіалізатор для retrieve"""
        if self.action == 'retrieve':
            return ListingDetailSerializer
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
