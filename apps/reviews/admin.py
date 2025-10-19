from django.contrib import admin
from .models import Review, ListingRating, OwnerRating


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'listing', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('customer__username', 'listing__title', 'comment')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Review Details', {
            'fields': ('booking', 'listing', 'customer', 'rating')
        }),
        ('Comments', {
            'fields': ('comment', 'owner_comment'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(ListingRating)
class ListingRatingAdmin(admin.ModelAdmin):
    list_display = ('listing', 'rater', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('listing__title', 'rater__username')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(OwnerRating)
class OwnerRatingAdmin(admin.ModelAdmin):
    list_display = ('owner', 'rater', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('owner__username', 'rater__username')
    readonly_fields = ('created_at', 'updated_at')