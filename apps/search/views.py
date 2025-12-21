from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Count, Q, Avg

from .models import SearchHistory
from .serializers import SearchQuerySerializer, SearchHistorySerializer, SearchSerializer
from apps.listings.models import Listing
from apps.listings.serializers import ListingListSerializer


class SearchQueryViewSet(viewsets.ViewSet):
    """ViewSet для популярних запитів"""
    permission_classes = [AllowAny]

    def list(self, request):
        """Повертає найпопулярніші пошукові запити"""
        from django.db import models

        popular_queries = SearchHistory.objects.values('query').annotate(
            count=Count('id'),
            avg_results=models.Avg('results_count')
        ).order_by('-count')[:10]

        return Response({
            'popular_queries': list(popular_queries),
            'total_searches': SearchHistory.objects.count()
        })


class SearchHistoryViewSet(viewsets.ModelViewSet):
    """ViewSet для історії пошуку"""
    serializer_class = SearchHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SearchHistory.objects.filter(user=self.request.user)

    @action(detail=False, methods=['delete'])
    def clear_all(self, request):
        """Очистити всю історію"""
        count = self.get_queryset().delete()[0]
        return Response({
            'message': f'Видалено {count} записів',
            'deleted': count
        })


class SearchViewSet(viewsets.ViewSet):
    """Головний ViewSet для пошуку"""
    permission_classes = [AllowAny]

    def list(self, request):
        """Пошук оголошень"""
        serializer = SearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        query = serializer.validated_data.get('query', '').strip()
        filters = serializer.validated_data

        # Базовий queryset
        listings = Listing.objects.filter(
            is_active=True,
            is_deleted=False
        )

        # Пошук по тексту
        if query:
            listings = listings.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(location__city__icontains=query) |
                Q(location__address__icontains=query)
            )

        # Фільтри
        if filters.get('min_price'):
            listings = listings.filter(price__gte=filters['min_price'])
        if filters.get('max_price'):
            listings = listings.filter(price__lte=filters['max_price'])
        if filters.get('city'):
            listings = listings.filter(location__city__icontains=filters['city'])
        if filters.get('rooms'):
            listings = listings.filter(rooms=filters['rooms'])
        if filters.get('property_type'):
            listings = listings.filter(property_type=filters['property_type'])

        results_count = listings.count()

        # Зберегти в історію кожен пошук (включаючи анонімних користувачів)
        filters_data = {
            k: v for k, v in filters.items()
            if k != 'query' and v not in (None, '', [])
        }

        if query or filters_data:
            SearchHistory.objects.create(
                user=request.user if request.user.is_authenticated else None,
                query=query,
                filters=filters_data,
                results_count=results_count,
            )
        SearchHistory.objects.create(
            user=request.user if request.user.is_authenticated else None,
            query=query,
            filters={k: v for k, v in filters.items() if k != 'query'},
            results_count=results_count
        )

        # Результат
        serializer = ListingListSerializer(listings, many=True, context={'request': request})
        return Response({
            'count': results_count,
            'results': serializer.data
        })
