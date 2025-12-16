from django.contrib import admin
from .models import Review, ListingRating, OwnerRating


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """
    Admin для відгуків

    Основні поля:
    - Рейтинг (1-5 зірок)
    - Коментар
    - Відповідь власника
    """

    list_display = (
        'id',
        'reviewer',
        'listing',
        'rating',
        'is_visible',
        'is_verified',
        'created_at'
    )

    list_filter = (
        'rating',
        'is_visible',
        'is_verified',
        'created_at'
    )

    search_fields = (
        'reviewer__username',
        'reviewer__email',
        'listing__title',
        'comment'
    )

    readonly_fields = (
        'created_at',
        'updated_at',
        'owner_response_at'
    )

    ordering = ['-created_at']

    fieldsets = (
        ('Основна інформація', {
            'fields': (
                'booking',
                'listing',
                'reviewer',
                'rating',
                'comment'
            )
        }),
        ('Відповідь власника', {
            'fields': (
                'owner_response',
                'owner_response_at'
            ),
            'classes': ('collapse',)
        }),
        ('Статус', {
            'fields': (
                'is_visible',
                'is_verified'
            )
        }),
        ('Дати', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )

    def save_model(self, request, obj, form, change):
        """Зберегти відгук і автоматично оновити рейтинги"""
        super().save_model(request, obj, form, change)
        # Рейтинги оновляться автоматично через метод save() моделі


@admin.register(ListingRating)
class ListingRatingAdmin(admin.ModelAdmin):
    """
    Admin для агрегованих рейтингів оголошень

    ✅ Показує середній рейтинг та статистику
    """

    list_display = (
        'listing',
        'average_rating',
        'total_reviews',
        'stars_5',
        'stars_4',
        'stars_3',
        'stars_2',
        'stars_1',
        'updated_at'
    )

    list_filter = (
        'average_rating',
        'total_reviews'
    )

    search_fields = (
        'listing__title',
        'listing__owner__username'
    )

    readonly_fields = (
        'listing',
        'average_rating',
        'total_reviews',
        'stars_5',
        'stars_4',
        'stars_3',
        'stars_2',
        'stars_1',
        'created_at',
        'updated_at',
        'get_rating_distribution'
    )

    ordering = ['-average_rating', '-total_reviews']

    fieldsets = (
        ('Оголошення', {
            'fields': ('listing',)
        }),
        ('Рейтинг', {
            'fields': (
                'average_rating',
                'total_reviews',
                'get_rating_distribution'
            )
        }),
        ('Розподіл за зірками', {
            'fields': (
                'stars_5',
                'stars_4',
                'stars_3',
                'stars_2',
                'stars_1'
            ),
            'classes': ('collapse',)
        }),
        ('Дати', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )

    def get_rating_distribution(self, obj):
        """Показати розподіл рейтингів у відсотках"""
        distribution = obj.rating_distribution
        html = '<div style="font-family: monospace;">'
        for stars in [5, 4, 3, 2, 1]:
            percentage = distribution[stars]
            bar_width = int(percentage * 2)  # масштаб для відображення
            bar = '█' * bar_width
            html += f'{stars}★: {bar} {percentage}%<br>'
        html += '</div>'
        return html

    get_rating_distribution.short_description = 'Розподіл рейтингів'
    get_rating_distribution.allow_tags = True

    def has_add_permission(self, request):
        """Заборонити створення вручну - створюється автоматично"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Заборонити видалення - оновлюється автоматично"""
        return False


@admin.register(OwnerRating)
class OwnerRatingAdmin(admin.ModelAdmin):
    """
    Admin для агрегованих рейтингів власників

    ✅ Показує середній рейтинг власника по всіх оголошеннях
    """

    list_display = (
        'owner',
        'average_rating',
        'total_reviews',
        'total_listings',
        'stars_5',
        'stars_4',
        'stars_3',
        'stars_2',
        'stars_1',
        'updated_at'
    )

    list_filter = (
        'average_rating',
        'total_reviews',
        'total_listings'
    )

    search_fields = (
        'owner__username',
        'owner__email',
        'owner__first_name',
        'owner__last_name'
    )

    readonly_fields = (
        'owner',
        'average_rating',
        'total_reviews',
        'total_listings',
        'stars_5',
        'stars_4',
        'stars_3',
        'stars_2',
        'stars_1',
        'created_at',
        'updated_at',
        'get_rating_distribution'
    )

    ordering = ['-average_rating', '-total_reviews']

    fieldsets = (
        ('Власник', {
            'fields': ('owner',)
        }),
        ('Рейтинг', {
            'fields': (
                'average_rating',
                'total_reviews',
                'total_listings',
                'get_rating_distribution'
            )
        }),
        ('Розподіл за зірками', {
            'fields': (
                'stars_5',
                'stars_4',
                'stars_3',
                'stars_2',
                'stars_1'
            ),
            'classes': ('collapse',)
        }),
        ('Дати', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )

    def get_rating_distribution(self, obj):
        """Показати розподіл рейтингів у відсотках"""
        distribution = obj.rating_distribution
        html = '<div style="font-family: monospace;">'
        for stars in [5, 4, 3, 2, 1]:
            percentage = distribution[stars]
            bar_width = int(percentage * 2)  # масштаб для відображення
            bar = '█' * bar_width
            html += f'{stars}★: {bar} {percentage}%<br>'
        html += '</div>'
        return html

    get_rating_distribution.short_description = 'Розподіл рейтингів'
    get_rating_distribution.allow_tags = True

    def has_add_permission(self, request):
        """Заборонити створення вручну - створюється автоматично"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Заборонити видалення - оновлюється автоматично"""
        return False


# ════════════════════════════════════════════════════════════════════
# ПРИМІТКИ
# ════════════════════════════════════════════════════════════════════

"""
✅ Review:
   - Рейтинг 1-5 зірок
   - Текстовий коментар
   - Відповідь власника
   - Автоматично оновлює ListingRating і OwnerRating при збереженні

✅ ListingRating:
   - Середній рейтинг оголошення
   - Кількість відгуків
   - Розподіл за зірками (5★, 4★, 3★, 2★, 1★)
   - Оновлюється автоматично
   - Read-only в admin (не можна редагувати вручну)

✅ OwnerRating:
   - Середній рейтинг власника (по всіх оголошеннях)
   - Загальна кількість відгуків
   - Кількість оголошень з відгуками
   - Розподіл за зірками (5★, 4★, 3★, 2★, 1★)
   - Оновлюється автоматично
   - Read-only в admin (не можна редагувати вручну)
"""
