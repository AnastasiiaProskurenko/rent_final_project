from django.contrib import admin
from django.utils.html import format_html
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Admin для сповіщень
    """

    list_display = [
        'id',
        'user',
        'title',
        'notification_type',
        'read_status',
        'created_at'
    ]

    list_filter = [
        'is_read',
        'notification_type',
        'created_at'
    ]

    search_fields = [
        'title',
        'message',
        'user__email',
        'user__first_name',
        'user__last_name'
    ]

    readonly_fields = [
        'created_at',
        'updated_at',
        'related_object_id',
        'related_object_type'
    ]

    fieldsets = (
        ('Основна інформація', {
            'fields': ('user', 'title', 'message')
        }),
        ('Тип та статус', {
            'fields': ('notification_type', 'is_read')
        }),
        ('Зв\'язані об\'єкти', {
            'fields': ('related_object_type', 'related_object_id'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_as_read', 'mark_as_unread', 'delete_read_notifications']

    def read_status(self, obj):
        """Візуальний статус прочитання"""
        if obj.is_read:
            return format_html(
                '<span style="color: green;">✓ Прочитано</span>'
            )
        return format_html(
            '<span style="color: red;">✉ Не прочитано</span>'
        )

    read_status.short_description = 'Статус'

    def mark_as_read(self, request, queryset):
        """Позначити як прочитане"""
        count = queryset.update(is_read=True)
        self.message_user(request, f'Позначено як прочитане: {count} сповіщень')

    mark_as_read.short_description = "✓ Позначити як прочитане"

    def mark_as_unread(self, request, queryset):
        """Позначити як непрочитане"""
        count = queryset.update(is_read=False)
        self.message_user(request, f'Позначено як непрочитане: {count} сповіщень')

    mark_as_unread.short_description = "✉ Позначити як непрочитане"

    def delete_read_notifications(self, request, queryset):
        """Видалити прочитані сповіщення"""
        read_notifications = queryset.filter(is_read=True)
        count = read_notifications.count()
        read_notifications.delete()
        self.message_user(request, f'Видалено прочитаних сповіщень: {count}')

    delete_read_notifications.short_description = "🗑️ Видалити прочитані"