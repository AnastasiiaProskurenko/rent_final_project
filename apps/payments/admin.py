from django.contrib import admin
from .models import Payment, Refund


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'booking',
        'amount',
        'status',
        'created_at'
    ]

    list_filter = [
        'status',
        'created_at'
    ]

    search_fields = [
        'booking__customer__email',
        'transaction_id'
    ]

    readonly_fields = [
        'booking',
        'amount',
        'transaction_id',
        'created_at',
        'updated_at'
    ]

    fieldsets = (
        ('Основна інформація', {
            'fields': ('booking', 'amount', 'status')
        }),
        ('Деталі транзакції', {
            'fields': ('transaction_id',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'payment',
        'amount',
        'status',
        'created_at'
    ]

    list_filter = [
        'status',
        'created_at'
    ]

    search_fields = [
        'payment__booking__customer__email',
        'reason'
    ]

    readonly_fields = [
        'payment',
        'amount',
        'created_at',
        'updated_at'
    ]

    fieldsets = (
        ('Основна інформація', {
            'fields': ('payment', 'amount', 'reason', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )