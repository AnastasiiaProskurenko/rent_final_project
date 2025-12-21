from django.db import models
from django.conf import settings
from apps.common.models import TimeModel


class SearchHistory(TimeModel):
    """
    Історія пошукових запитів користувачів

    Зберігає:
    - Пошуковий запит
    - Застосовані фільтри
    - Кількість результатів
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='search_history',
        null=True,
        blank=True,
        verbose_name='Користувач'
    )

    query = models.CharField(
        max_length=255,
        verbose_name='Пошуковий запит',
        help_text='Ключові слова для пошуку'
    )

    filters = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Фільтри',
        help_text='Застосовані фільтри (ціна, локація, тип і т.д.)'
    )

    results_count = models.IntegerField(
        default=0,
        verbose_name='Кількість результатів',
        help_text='Скільки оголошень знайдено'
    )

    class Meta:
        verbose_name = 'Історія пошуку'
        verbose_name_plural = 'Історія пошуків'
        ordering = ['-created_at']
        db_table = 'search_searchhistory'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['query']),
        ]

    def __str__(self):
        user_str = self.user.email if self.user else 'Анонім'
        return f"{user_str} - {self.query} ({self.results_count} результатів)"


# Alias для сумісності з serializers
SearchQuery = SearchHistory
