from django.contrib import admin
from .models import Listing, ListingPhoto


class ListingPhotoInline(admin.TabularInline):
    model = ListingPhoto
    extra = 0
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'price', 'city', 'num_rooms', 'max_guests', 'is_active', 'created_at')
    list_filter = ('is_active', 'pets_allowed', 'country', 'city', 'category', 'created_at')
    search_fields = ('title', 'description', 'owner__username', 'city', 'street')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [ListingPhotoInline]
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('owner', 'title', 'description', 'price', 'category', 'is_active')
        }),
        ('Property Details', {
            'fields': ('num_rooms', 'max_guests', 'pets_allowed')
        }),
        ('Location', {
            'fields': ('country', 'city', 'district', 'street', 'house_number', 'apartment_number')
        }),
        ('Amenities', {
            'fields': ('has_air_conditioning', 'has_tv', 'has_minibar', 'has_fridge', 
                      'has_kitchen', 'has_bathroom', 'has_washing_machine', 
                      'has_hair_dryer', 'hygiene_products', 'has_parking'),
            'classes': ('collapse',)
        }),
        ('Distances', {
            'fields': ('distance_to_center', 'distance_to_sea'),
            'classes': ('collapse',)
        }),
        ('Images', {
            'fields': ('main_image',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(ListingPhoto)
class ListingPhotoAdmin(admin.ModelAdmin):
    list_display = ('listing', 'image', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('listing__title',)
    readonly_fields = ('created_at', 'updated_at')