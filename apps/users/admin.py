from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile, RefreshTokenRecord


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_verified', 'is_active', 'date_joined')
    list_filter = ('role', 'is_verified', 'is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'is_verified')}),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'languages', 'listing_count', 'rating')
    list_filter = ('languages',)
    search_fields = ('user__username', 'user__email', 'phone')
    readonly_fields = ('listing_count', 'rating')


@admin.register(RefreshTokenRecord)
class RefreshTokenRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'jti', 'revoked', 'expires_at', 'created_at')
    list_filter = ('revoked', 'created_at')
    search_fields = ('user__username', 'jti')
    readonly_fields = ('created_at', 'updated_at')