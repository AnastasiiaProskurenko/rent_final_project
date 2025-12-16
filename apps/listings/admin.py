from django.contrib import admin
from .models import Listing, ListingPhoto, Amenity


class ListingPhotoInline(admin.TabularInline):
    model = ListingPhoto
    extra = 1
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'title',
        'owner',
        'price',
        'city',
        'property_type',
        'is_active',
        'created_at'
    ]

    list_filter = [
        'is_active',
        'property_type',
        'created_at'
    ]

    search_fields = [
        'title',
        'description',
        'owner__email',
        'city'
    ]

    readonly_fields = ['created_at', 'updated_at']
    inlines = [ListingPhotoInline]


@admin.register(ListingPhoto)
class ListingPhotoAdmin(admin.ModelAdmin):
    list_display = ['id', 'listing', 'created_at']
    list_filter = ['created_at']
    search_fields = ['listing__title']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'created_at']
    search_fields = ['name']
    list_filter = ['created_at']
    readonly_fields = ['created_at', 'updated_at']