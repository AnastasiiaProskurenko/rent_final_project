from django.contrib import admin
from .models import SearchQuery, SearchHistory


@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    list_display = ('query', 'user', 'count', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('query', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Search Query', {
            'fields': ('query', 'user', 'count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'query', 'ip', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('query', 'user__username', 'ip')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Search History', {
            'fields': ('user', 'query', 'ip')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )