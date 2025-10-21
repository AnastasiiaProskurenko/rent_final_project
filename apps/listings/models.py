from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from apps.common.file_path import image_listing_upload_to
from apps.common.models import TimeModel
from apps.common.enums import AmenityStatus

User = get_user_model()

class Listing(TimeModel):

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listings', verbose_name='owner')
    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, validators= [MinValueValidator(0.01, message='Price must be more than 0') ])

    num_rooms = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    max_guests = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    pets_allowed = models.BooleanField(default=False)

    country = models.CharField(max_length=50, default='Germany')
    city = models.CharField(max_length=100)
    district = models.CharField(max_length=100, blank=True, null=True)
    street = models.CharField(max_length=100)
    house_number = models.CharField(max_length=20)
    apartment_number = models.CharField(max_length=20, blank=True, null=True)

    air_conditioning = models.CharField(max_length=10, choices=AmenityStatus.choices, default=AmenityStatus.UNKNOWN, verbose_name='Air conditioning ')
    tv = models.CharField(max_length=10, choices=AmenityStatus.choices, default=AmenityStatus.UNKNOWN, verbose_name='TV ')
    minibar = models.CharField(max_length=10, choices=AmenityStatus.choices, default=AmenityStatus.UNKNOWN, verbose_name='Minibar ')
    fridge = models.CharField(max_length=10, choices=AmenityStatus.choices, default=AmenityStatus.UNKNOWN, verbose_name='Refrigerator ')
    kitchen = models.CharField(max_length=10, choices=AmenityStatus.choices, default=AmenityStatus.UNKNOWN, verbose_name='Kitchen ')
    bathroom = models.CharField(max_length=10, choices=AmenityStatus.choices, default=AmenityStatus.UNKNOWN, verbose_name='Bathroom ')
    washing_machine = models.CharField(max_length=10, choices=AmenityStatus.choices, default=AmenityStatus.UNKNOWN, verbose_name='Washing machine ')
    hair_dryer = models.CharField(max_length=10, choices=AmenityStatus.choices, default=AmenityStatus.UNKNOWN, verbose_name='Hairdryer ')
    hygiene_products = models.CharField(max_length=10, choices=AmenityStatus.choices, default=AmenityStatus.UNKNOWN, verbose_name='Toiletries ')
    parking = models.CharField(max_length=10, choices=AmenityStatus.choices, default=AmenityStatus.UNKNOWN, verbose_name='Parking')

    distance_to_center = models.FloatField(blank=True, null=True)
    distance_to_sea = models.FloatField(blank=True, null=True)

    category = models.CharField(max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    main_image = models.ImageField(upload_to=image_listing_upload_to, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} ({self.owner.get_full_name()})'


class ListingPhoto(TimeModel):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='photos', verbose_name='listing')
    image = models.ImageField(upload_to=image_listing_upload_to)

    def clean(self):
        super().clean()

        if self.listing:
            existing_photos = self.listing.photos.exclude(pk=self.pk).count()
            if existing_photos >=8:
                from django.core.exceptions import ValidationError
                raise ValidationError('8 images are maximum',code='max_photos_limit')

    def save(self, *args, **kwargs):

        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Photo {self.id} for {self.listing.title}'