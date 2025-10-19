from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db import models
from .models import SearchQuery, SearchHistory
from .serializers import SearchQuerySerializer, SearchHistorySerializer, SearchSerializer
from apps.listings.models import Listing


class SearchQueryViewSet(viewsets.ModelViewSet):
    queryset = SearchQuery.objects.all()
    serializer_class = SearchQuerySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['user', 'query']
    search_fields = ['query']
    ordering_fields = ['count', 'created_at']
    ordering = ['-count', '-created_at']
    
    def get_queryset(self):
        return SearchQuery.objects.select_related('user')


class SearchHistoryViewSet(viewsets.ModelViewSet):
    queryset = SearchHistory.objects.all()
    serializer_class = SearchHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['user', 'query']
    search_fields = ['query']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return SearchHistory.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class SearchViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]
    
    @action(detail=False, methods=['post'])
    def search_listings(self, request):

        serializer = SearchSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        query = serializer.validated_data['query']
        filters = serializer.validated_data.get('filters', {})
        

        listings = Listing.objects.filter(is_active=True)
        

        if query:
            listings = listings.filter(
                models.Q(title__icontains=query) |
                models.Q(description__icontains=query) |
                models.Q(city__icontains=query) |
                models.Q(country__icontains=query)
            )
        

        if 'city' in filters:
            listings = listings.filter(city__icontains=filters['city'])
        if 'country' in filters:
            listings = listings.filter(country__icontains=filters['country'])
        if 'min_price' in filters:
            listings = listings.filter(price__gte=filters['min_price'])
        if 'max_price' in filters:
            listings = listings.filter(price__lte=filters['max_price'])
        if 'num_rooms' in filters:
            listings = listings.filter(num_rooms__gte=filters['num_rooms'])
        if 'max_guests' in filters:
            listings = listings.filter(max_guests__gte=filters['max_guests'])
        if 'pets_allowed' in filters:
            listings = listings.filter(pets_allowed=filters['pets_allowed'])
        

        amenity_fields = [
            'has_air_conditioning', 'has_tv', 'has_minibar', 'has_fridge',
            'has_kitchen', 'has_bathroom', 'has_washing_machine',
            'has_hair_dryer', 'hygiene_products', 'has_parking'
        ]
        
        for field in amenity_fields:
            if field in filters and filters[field] is True:
                listings = listings.filter(**{field: True})
        

        if request.user.is_authenticated:
            search_query, created = SearchQuery.objects.get_or_create(
                query=query,
                user=request.user,
                defaults={'count': 1}
            )
            if not created:
                search_query.count += 1
                search_query.save()
            

            SearchHistory.objects.create(
                user=request.user,
                query=query,
                ip=request.META.get('REMOTE_ADDR')
            )


        from apps.listings.serializers import ListingSerializer
        serializer = ListingSerializer(listings[:50], many=True)  # Limit to 50 results
        
        return Response({
            'query': query,
            'results': serializer.data,
            'total_count': listings.count()
        })
    
    @action(detail=False, methods=['get'])
    def popular_searches(self, request):

        popular = SearchQuery.objects.order_by('-count')[:10]
        serializer = SearchQuerySerializer(popular, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_search_history(self, request):

        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        history = SearchHistory.objects.filter(user=request.user)[:20]
        serializer = SearchHistorySerializer(history, many=True)
        return Response(serializer.data)