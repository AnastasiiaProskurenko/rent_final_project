from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.contrib.auth import get_user_model

from apps.common.models import TimeModel
from apps.common.enums import PaymentStatus, PaymentMethod

User = get_user_model()


class Payment(TimeModel):
    """
    Модель платежу
    ✅ З валідаторами для всіх числових полів
    """

    booking = models.OneToOneField(
        'bookings.Booking',
        on_delete=models.CASCADE,
        related_name='payment',
        verbose_name='Booking'
    )
    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name='Customer'
    )

    # ✅ ЧИСЛОВІ ПОЛЯ З ВАЛІДАТОРАМИ

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(0.01, message='Сума має бути більше 0'),
            MaxValueValidator(9999999.99, message='Сума занадто велика')
        ],
        verbose_name='Amount',
        help_text='Сума платежу (0.01 - 9,999,999.99)'
    )

    # Метод оплати
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CARD,
        verbose_name='Payment Method'
    )

    # Статус
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        verbose_name='Status'
    )

    # Інформація про транзакцію
    transaction_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=True,
        verbose_name='Transaction ID',
        help_text='ID транзакції з платіжної системи'
    )

    payment_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Payment Date',
        help_text='Дата фактичної оплати'
    )

    # Додаткова інформація
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='Notes'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        indexes = [
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['booking']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f'Payment #{self.id} - {self.amount} ({self.status})'

    def clean(self):
        """Валідація платежу"""
        super().clean()

        # Перевірка що сума співпадає з бронюванням
        if self.booking and self.amount != self.booking.total_price:
            from django.core.exceptions import ValidationError
            raise ValidationError(
                f'Payment amount ({self.amount}) must match booking total price ({self.booking.total_price})'
            )

    def save(self, *args, **kwargs):
        """Збереження з валідацією"""
        self.full_clean()
        super().save(*args, **kwargs)


class Refund(TimeModel):
    """
    Модель повернення коштів
    ✅ З валідаторами для всіх числових полів
    """

    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='refunds',
        verbose_name='Payment'
    )

    # ✅ ЧИСЛОВІ ПОЛЯ З ВАЛІДАТОРАМИ

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(0.01, message='Сума повернення має бути більше 0'),
            MaxValueValidator(9999999.99, message='Сума повернення занадто велика')
        ],
        verbose_name='Refund Amount',
        help_text='Сума повернення (0.01 - 9,999,999.99)'
    )

    # Статус
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        verbose_name='Refund Status'
    )

    # Інформація про повернення
    refund_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Refund Date'
    )

    reason = models.TextField(
        verbose_name='Refund Reason'
    )

    transaction_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Refund Transaction ID'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Refund'
        verbose_name_plural = 'Refunds'
        indexes = [
            models.Index(fields=['payment', 'status']),
        ]

    def __str__(self):
        return f'Refund #{self.id} - {self.amount} for Payment #{self.payment.id}'

    def clean(self):
        """Валідація повернення"""
        super().clean()

        # Перевірка що сума повернення не перевищує суму платежу
        if self.payment and self.amount > self.payment.amount:
            from django.core.exceptions import ValidationError
            raise ValidationError(
                f'Refund amount ({self.amount}) cannot exceed payment amount ({self.payment.amount})'
            )

        # Перевірка що загальна сума повернень не перевищує суму платежу
        if self.payment:
            total_refunded = sum(
                r.amount for r in self.payment.refunds.exclude(pk=self.pk)
                if r.status == PaymentStatus.COMPLETED
            )

            if total_refunded + self.amount > self.payment.amount:
                from django.core.exceptions import ValidationError
                raise ValidationError(
                    f'Total refund amount ({total_refunded + self.amount}) '
                    f'cannot exceed payment amount ({self.payment.amount})'
                )

    def save(self, *args, **kwargs):
        """Збереження з валідацією"""
        self.full_clean()
        super().save(*args, **kwargs)
