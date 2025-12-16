from django.contrib import admin
from .models import ListingView


@admin.register(ListingView)
class ListingViewAdmin(admin.ModelAdmin):
    list_display = ['id', 'listing', 'user', 'created_at']
    list_filter = ['created_at']
    search_fields = ['listing__title', 'user__email']
    readonly_fields = ['listing', 'user', 'created_at', 'updated_at']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False