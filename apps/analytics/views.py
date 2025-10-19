from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from django.db.models import Count, Avg
from .models import ListingView
from .serializers import ListingViewSerializer


class ListingViewViewSet(viewsets.ModelViewSet):
    queryset = ListingView.objects.all()
    serializer_class = ListingViewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['listing', 'user']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return ListingView.objects.select_related('listing', 'user')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user if self.request.user.is_authenticated else None)

    @action(detail=False, methods=['get'])
    def listing_stats(self, request):

        listing_id = request.query_params.get('listing_id')
        if not listing_id:
            return Response(
                {'error': 'listing_id parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )


        views = ListingView.objects.filter(listing_id=listing_id)
        total_views = views.count()
        unique_views = views.values('ip').distinct().count()


        from django.utils import timezone
        from datetime import timedelta

        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_views = views.filter(created_at__gte=thirty_days_ago).count()

        return Response({
            'listing_id': listing_id,
            'total_views': total_views,
            'unique_views': unique_views,
            'recent_views_30d': recent_views
        })

    @action(detail=False, methods=['get'])
    def popular_listings(self, request):

        popular = ListingView.objects.values('listing').annotate(
            view_count=Count('id')
        ).order_by('-view_count')[:10]


        from apps.listings.serializers import ListingSerializer
        from apps.listings.models import Listing

        listing_ids = [item['listing'] for item in popular]
        listings = Listing.objects.filter(id__in=listing_ids)


        result = []
        for listing in listings:
            view_count = next(
                (item['view_count'] for item in popular if item['listing'] == listing.id), 0
            )
            listing_data = ListingSerializer(listing).data
            listing_data['view_count'] = view_count
            result.append(listing_data)

        return Response(result)


    @action(detail=False, methods=['get'])
    def most_booked_listings(self, request):

        from apps.bookings.models import Booking
        from apps.listings.models import Listing
        from apps.listings.serializers import ListingSerializer


        popular = Booking.objects.filter(
            status__in=['agreed', 'ended']
        ).values('listing').annotate(
            booking_count=Count('id')
        ).order_by('-booking_count')[:10]

        listing_ids = [item['listing'] for item in popular]
        listings = Listing.objects.filter(id__in=listing_ids)

        result = []
        for listing in listings:
            booking_count = next(
                (item['booking_count'] for item in popular if item['listing'] == listing.id), 0
            )
            listing_data = ListingSerializer(listing).data
            listing_data['booking_count'] = booking_count
            result.append(listing_data)


        result = sorted(result, key=lambda x: x['booking_count'], reverse=True)

        return Response(result)

    @action(detail=False, methods=['get'])
    def user_activity(self, request):

        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        views = self.get_queryset().filter(user=request.user)
        serializer = self.get_serializer(views, many=True)
        return Response(serializer.data)