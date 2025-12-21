from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ListingViewViewSet

app_name = 'analytics'

router = DefaultRouter()
router.register(r'listing-views', ListingViewViewSet, basename='listingview')

urlpatterns = [
    path('', include(router.urls)),
]

"""
═══════════════════════════════════════════════════════════════════════════
                          ДОСТУПНІ URLS ДЛЯ ANALYTICS
═══════════════════════════════════════════════════════════════════════════

БАЗОВІ ENDPOINTS:
──────────────────────────────────────────────────────────────────────────
GET     /api/listing-views/                           - Список переглядів
GET     /api/listing-views/{id}/                      - Деталі перегляду

CUSTOM ACTIONS:
──────────────────────────────────────────────────────────────────────────
GET     /api/listing-views/popular_listings/          - Топ-10 популярних
GET     /api/listing-views/my_views/                  - Останні перегляди користувача
GET     /api/listing-views/my_listings_stats/         - Статистика переглядів моїх оголошень

═══════════════════════════════════════════════════════════════════════════
"""

