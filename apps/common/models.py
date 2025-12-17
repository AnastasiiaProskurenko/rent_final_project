from django.db import models
from django.utils import timezone
from django.db.models import UniqueConstraint

from apps.common.constants import (
    ADDRESS_MAX_LENGTH,
    CITY_MAX_LENGTH,
    COUNTRY_MAX_LENGTH,
    LATITUDE_DECIMAL_PLACES,
    LATITUDE_MAX_DIGITS,
    LONGITUDE_DECIMAL_PLACES,
    LONGITUDE_MAX_DIGITS,
)

class TimeModel(models.Model):

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    class Meta:
        abstract = True


class Location(TimeModel):
    """
    Загальна модель для збереження адреси та координат.
    Використовується як зовнішнє посилання для оголошень і бронювань.
    """

    country = models.CharField(
        max_length=COUNTRY_MAX_LENGTH,
        verbose_name='Country'
    )
    city = models.CharField(
        max_length=CITY_MAX_LENGTH,
        verbose_name='City'
    )
    address = models.CharField(
        max_length=ADDRESS_MAX_LENGTH,
        verbose_name='Street Address'
    )
    normalized_address = models.CharField(
        max_length=ADDRESS_MAX_LENGTH,
        editable=False,
        verbose_name='Normalized Address'
    )
    latitude = models.DecimalField(
        max_digits=LATITUDE_MAX_DIGITS,
        decimal_places=LATITUDE_DECIMAL_PLACES,
        null=True,
        blank=True,
        verbose_name='Latitude'
    )
    longitude = models.DecimalField(
        max_digits=LONGITUDE_MAX_DIGITS,
        decimal_places=LONGITUDE_DECIMAL_PLACES,
        null=True,
        blank=True,
        verbose_name='Longitude'
    )

    class Meta:
        ordering = ['city', 'country']
        verbose_name = 'Location'
        verbose_name_plural = 'Locations'
        indexes = [
            models.Index(fields=['city', 'country']),
            models.Index(fields=['normalized_address']),
        ]
        constraints = [
            UniqueConstraint(
                fields=['country', 'city', 'normalized_address'],
                name='unique_normalized_location'
            )
        ]

    def __str__(self):
        return f'{self.address}, {self.city}, {self.country}'

    def save(self, *args, **kwargs):
        self.country = self.country.strip()
        self.city = self.city.strip()
        self.address = self.address.strip()
        self.normalized_address = self.normalize_address(self.address)
        super().save(*args, **kwargs)

    @staticmethod
    def normalize_address(address: str) -> str:
        """
        Нормалізує адресу для уникнення дублів у базі.
        """
        if not address:
            return ''

        normalized = ' '.join(address.split())
        normalized = normalized.lower().replace('.', '')

        replacements = {
            'вулиця': 'вул',
            'вул ': 'вул',
            'проспект': 'просп',
            'площа': 'пл',
            'провулок': 'пров',
            'будинок': 'буд',
            'буд ': 'буд',
            'квартира': 'кв',
            'кв ': 'кв',
        }

        for old, new in replacements.items():
            normalized = normalized.replace(old, new)

        return normalized.strip()
