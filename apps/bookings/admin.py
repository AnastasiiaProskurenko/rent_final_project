from django.contrib import admin
from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'listing',
        'customer',
        'check_in',
        'check_out',
        'status',
        'total_price',
        'created_at'
    ]

    list_filter = [
        'status',
        'check_in',
        'check_out',
        'created_at'
    ]

    search_fields = [
        'listing__title',
        'customer__email',
        'customer__first_name',
        'customer__last_name'
    ]

    readonly_fields = [
        'customer',
        'total_price',
        'created_at',
        'updated_at'
    ]

    list_select_related = ['customer', 'listing']  # ✅ Правильно

    fieldsets = (
        ('Бронювання', {
            'fields': ('listing', 'customer', 'status')
        }),
        ('Дати', {
            'fields': ('check_in', 'check_out')
        }),
        ('Деталі', {
            'fields': ('num_guests', 'total_price')
        }),
        ('Скасування', {
            'fields': ('cancellation_reason',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('customer', 'listing')