import django_filters
from .models import Listing


class ListingFilter(django_filters.FilterSet):
    # 🔹 ЯВНИЙ фільтр для параметра ?city=
    city = django_filters.CharFilter(
        field_name='location__city',
        lookup_expr='iexact'
    )

    # 🔹 Фільтр за ціною
    min_price = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='gte'
    )
    max_price = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='lte'
    )

    owner = django_filters.NumberFilter(field_name='owner_id')

    class Meta:
        model = Listing
        fields = [
            'city',          # ← тепер ?city= працює
            'price',
            'is_active',
            'owner',
        ]