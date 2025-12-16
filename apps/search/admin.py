from django.contrib import admin
from .models import SearchHistory


@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'query', 'results_count', 'created_at']
    list_filter = ['created_at', 'results_count']
    search_fields = ['query', 'user__email']
    readonly_fields = ['created_at', 'updated_at', 'filters']

    def has_add_permission(self, request):
        return False