import django_filters
from .models import Booking
from apps.common.enums import BookingStatus


class BookingFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=BookingStatus.choices)
    check_in = django_filters.DateFilter()
    check_in__gte = django_filters.DateFilter(field_name='check_in', lookup_expr='gte')
    check_in__lte = django_filters.DateFilter(field_name='check_in', lookup_expr='lte')
    check_out = django_filters.DateFilter()
    check_out__gte = django_filters.DateFilter(field_name='check_out', lookup_expr='gte')
    check_out__lte = django_filters.DateFilter(field_name='check_out', lookup_expr='lte')
    customer = django_filters.NumberFilter(field_name='customer__id')
    listing = django_filters.NumberFilter(field_name='listing__id')
    min_price = django_filters.NumberFilter(field_name='total_price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='total_price', lookup_expr='lte')
    
    class Meta:
        model = Booking
        fields = ['status', 'check_in', 'check_out', 'customer', 'listing', 'min_price', 'max_price']

