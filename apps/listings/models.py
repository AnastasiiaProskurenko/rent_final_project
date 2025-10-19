from django.db import models
from django.core.validators import MinValueValidator

from apps.common.file_path import image_listing_upload_to
from apps.common.models import TimeModel
from django.contrib.auth import get_user_model

User = get_user_model()

class Listing(TimeModel):

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listings', verbose_name='owner')
    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    num_rooms = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    max_guests = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    pets_allowed = models.BooleanField(default=False)

    country = models.CharField(max_length=50, default='Germany')
    city = models.CharField(max_length=100)
    district = models.CharField(max_length=100, blank=True, null=True)
    street = models.CharField(max_length=100)
    house_number = models.CharField(max_length=20)
    apartment_number = models.CharField(max_length=20, blank=True, null=True)


    has_air_conditioning = models.BooleanField(null=True, default=None)
    has_tv = models.BooleanField(null=True, default=None)
    has_minibar = models.BooleanField(null=True, default=None)
    has_fridge = models.BooleanField(null=True, default=None)
    has_kitchen = models.BooleanField(null=True, default=None)
    has_bathroom = models.BooleanField(null=True, default=None)
    has_washing_machine = models.BooleanField(null=True, default=None)
    has_hair_dryer = models.BooleanField(null=True, default=None)
    hygiene_products = models.BooleanField(null=True, default=None)
    has_parking = models.BooleanField(null=True, default=None)

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

    def save(self, *args, **kwargs):

        if self.listing.photos.exclude(pk=self.pk).count() >= 8:
            raise ValueError('8 images are maximum')
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Photo {self.id} for {self.listing.title}'