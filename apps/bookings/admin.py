from django.contrib import admin
from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'listing', 'check_in', 'check_out', 'num_guests', 'total_price', 'status', 'created_at')
    list_filter = ('status', 'check_in', 'check_out', 'created_at')
    search_fields = ('customer__username', 'listing__title', 'notes')
    readonly_fields = ('total_price', 'created_at', 'updated_at')
    date_hierarchy = 'check_in'
    
    fieldsets = (
        ('Booking Details', {
            'fields': ('customer', 'listing', 'status', 'created_by')
        }),
        ('Dates & Times', {
            'fields': ('check_in', 'check_out', 'check_in_time', 'check_out_time')
        }),
        ('Guests & Pricing', {
            'fields': ('num_guests', 'total_price')
        }),
        ('Additional Info', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('customer', 'listing', 'created_by')