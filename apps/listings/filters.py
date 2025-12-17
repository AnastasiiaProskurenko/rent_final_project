import django_filters
from .models import Listing


class ListingFilter(django_filters.FilterSet):
    """
    Простий фільтр для оголошень

    Використовує тільки базові поля, які точно є в моделі
    """

    # Фільтр за ціною
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')

    class Meta:
        model = Listing
        fields = {
            'location__city': ['exact', 'icontains'],
            'price': ['exact', 'gte', 'lte'],
            'is_active': ['exact'],
        }


# ════════════════════════════════════════════════════════════════════
# ПРИМІТКИ
# ════════════════════════════════════════════════════════════════════

"""
СПРОЩЕНА ВЕРСІЯ
──────────────────────────────────────────────────────────────────────

Використовує тільки 100% наявні поля:
- city
- price
- is_active

Додайте інші поля відповідно до вашої моделі Listing!


ПРИКЛАДИ:
──────────────────────────────────────────────────────────────────────

GET /api/listings/?city=Berlin
GET /api/listings/?min_price=100&max_price=500
GET /api/listings/?is_active=true
"""
