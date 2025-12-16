from django.db import models
from django.conf import settings
from apps.common.models import TimeModel


class Notification(TimeModel):
    """
    Сповіщення для користувачів

    Типи сповіщень:
    - BOOKING: Нове бронювання, підтвердження, скасування
    - REVIEW: Новий відгук на оголошення
    - PAYMENT: Платіж отриманий/повернутий
    - MESSAGE: Повідомлення від адміністратора
    - SYSTEM: Системні сповіщення
    """

    NOTIFICATION_TYPES = [
        ('BOOKING', 'Бронювання'),
        ('REVIEW', 'Відгук'),
        ('PAYMENT', 'Платіж'),
        ('MESSAGE', 'Повідомлення'),
        ('SYSTEM', 'Системне'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Користувач'
    )

    title = models.CharField(
        max_length=255,
        verbose_name='Заголовок'
    )

    message = models.TextField(
        verbose_name='Повідомлення',
        help_text='Детальний текст сповіщення'
    )

    notification_type = models.CharField(
        max_length=50,
        choices=NOTIFICATION_TYPES,
        default='SYSTEM',
        verbose_name='Тип сповіщення'
    )

    is_read = models.BooleanField(
        default=False,
        verbose_name='Прочитано',
        help_text='Чи переглянув користувач це сповіщення'
    )

    related_object_id = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='ID пов\'язаного об\'єкта',
        help_text='ID бронювання, відгуку або іншого об\'єкта'
    )

    related_object_type = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='Тип пов\'язаного об\'єкта',
        help_text='booking, review, payment і т.д.'
    )

    class Meta:
        verbose_name = 'Сповіщення'
        verbose_name_plural = 'Сповіщення'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
        ]

    def __str__(self):
        status = '✓' if self.is_read else '✉'
        return f"{status} {self.user.email} - {self.title}"

    @classmethod
    def create_booking_notification(cls, booking, title, message):
        """Створити сповіщення про бронювання"""
        return cls.objects.create(
            user=booking.customer,
            title=title,
            message=message,
            notification_type='BOOKING',
            related_object_id=booking.id,
            related_object_type='booking'
        )

    @classmethod
    def create_review_notification(cls, review, title, message):
        """Створити сповіщення про відгук"""
        return cls.objects.create(
            user=review.listing.owner,
            title=title,
            message=message,
            notification_type='REVIEW',
            related_object_id=review.id,
            related_object_type='review'
        )