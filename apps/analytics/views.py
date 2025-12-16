from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Q

from .models import ListingView
from .serializers import ListingViewSerializer
from apps.listings.serializers import ListingListSerializer


class ListingViewViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для статистики переглядів

    Endpoints:
    - GET /listing-views/ - Список переглядів
    - GET /listing-views/{id}/ - Деталі перегляду
    - GET /listing-views/popular_listings/ - Популярні оголошення
    - GET /listing-views/my_views/ - Мої перегляди
    """

    serializer_class = ListingViewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Адміни бачать все, користувачі - тільки свої
        """
        user = self.request.user

        if user.is_staff or user.is_superuser:
            return ListingView.objects.all()

        return ListingView.objects.filter(
            Q(user=user) | Q(listing__owner=user)
        )

    @action(detail=False, methods=['get'])
    def popular_listings(self, request):
        """
        Топ-10 найпопулярніших оголошень
        """
        from apps.listings.models import Listing

        # Рахуємо перегляди для кожного listing
        popular = ListingView.objects.values('listing').annotate(
            views_count=Count('id')
        ).order_by('-views_count')[:10]

        # Отримуємо самі listing
        listing_ids = [item['listing'] for item in popular]
        listings = Listing.objects.filter(id__in=listing_ids)

        # Додаємо кількість переглядів
        views_dict = {item['listing']: item['views_count'] for item in popular}

        serializer = ListingListSerializer(listings, many=True, context={'request': request})
        data = serializer.data

        # Додаємо views_count до кожного
        for item in data:
            item['views_count'] = views_dict.get(item['id'], 0)

        # Сортуємо по views_count
        data = sorted(data, key=lambda x: x['views_count'], reverse=True)

        return Response(data)

    @action(detail=False, methods=['get'])
    def my_views(self, request):
        """
        Мої перегляди (історія)
        """
        views = ListingView.objects.filter(user=request.user).order_by('-viewed_at')[:20]
        serializer = self.get_serializer(views, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_listings_stats(self, request):
        """
        Статистика переглядів моїх оголошень
        """
        from apps.listings.models import Listing

        # Мої оголошення
        my_listings = Listing.objects.filter(owner=request.user)

        # Рахуємо перегляди
        stats = []
        for listing in my_listings:
            views_count = ListingView.objects.filter(listing=listing).count()
            unique_users = ListingView.objects.filter(
                listing=listing
            ).values('user').distinct().count()

            stats.append({
                'listing_id': listing.id,
                'listing_title': listing.title,
                'total_views': views_count,
                'unique_viewers': unique_users
            })

        # Сортуємо по кількості переглядів
        stats = sorted(stats, key=lambda x: x['total_views'], reverse=True)

        return Response({
            'total_listings': my_listings.count(),
            'listings_stats': stats
        })