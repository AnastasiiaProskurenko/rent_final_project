from django.contrib import admin
from .models import ListingView


@admin.register(ListingView)
class ListingViewAdmin(admin.ModelAdmin):
    list_display = ('id', 'listing', 'user', 'ip', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('listing__title', 'user__username', 'ip', 'user_agent')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('View Details', {
            'fields': ('listing', 'user', 'ip', 'user_agent')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('listing', 'user')