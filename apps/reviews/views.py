from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Review, ListingRating, OwnerRating
from .serializers import ReviewSerializer, ListingRatingSerializer, OwnerRatingSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['listing', 'customer', 'rating']
    search_fields = ['comment', 'owner_comment']
    ordering_fields = ['created_at', 'rating']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return Review.objects.select_related('customer', 'listing', 'booking')
    
    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_reviews(self, request):

        reviews = self.get_queryset().filter(customer=request.user)
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def listing_reviews(self, request):

        listing_id = request.query_params.get('listing_id')
        if not listing_id:
            return Response(
                {'error': 'listing_id parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reviews = self.get_queryset().filter(listing_id=listing_id)
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)


class ListingRatingViewSet(viewsets.ModelViewSet):
    queryset = ListingRating.objects.all()
    serializer_class = ListingRatingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['listing', 'rater', 'rating']
    ordering_fields = ['created_at', 'rating']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return ListingRating.objects.select_related('listing', 'rater', 'review')
    
    def perform_create(self, serializer):
        serializer.save(rater=self.request.user)


class OwnerRatingViewSet(viewsets.ModelViewSet):
    queryset = OwnerRating.objects.all()
    serializer_class = OwnerRatingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['owner', 'rater', 'rating']
    ordering_fields = ['created_at', 'rating']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return OwnerRating.objects.select_related('owner', 'rater')
    
    def perform_create(self, serializer):
        serializer.save(rater=self.request.user)