from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile, RefreshTokenRecord


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_groups', 'is_active', 'date_joined')
    list_filter = ('groups',  'is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'groups'),
        }),
    )

    filter_horizontal = ('groups', 'user_permissions')

    def get_groups(self, obj):
        groups = ', '.join([g.name for g in obj.groups.all()])
        return groups if groups else 'No group'

    get_groups.short_description = 'Groups'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'languages', 'listing_count', 'rating')
    list_filter = ('languages',)
    search_fields = ('user__username', 'user__email', 'phone')
    readonly_fields = ('listing_count', 'rating')
    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('Contact', {'fields': ('phone', 'languages')}),
        ('Profile', {'fields': ('avatar', 'biography')}),
    )


@admin.register(RefreshTokenRecord)
class RefreshTokenRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'jti', 'revoked', 'expires_at', 'created_at')
    list_filter = ('revoked', 'created_at')
    search_fields = ('user__username', 'jti')
    readonly_fields = ('created_at', 'updated_at')
