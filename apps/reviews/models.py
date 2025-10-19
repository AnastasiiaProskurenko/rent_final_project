from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Avg

from apps.common.models import TimeModel
from django.contrib.auth import get_user_model

User = get_user_model()

class Review(TimeModel):

    booking = models.OneToOneField('bookings.Booking', on_delete=models.CASCADE, related_name='review', verbose_name='booking')
    listing = models.ForeignKey('listings.Listing', on_delete=models.CASCADE, related_name='reviews', verbose_name='listing')
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews', verbose_name='customer')

    rating = models.PositiveSmallIntegerField(default=5)
    comment = models.TextField(blank=True, null=True)

    owner_comment = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        ordering = ['-created_at']



    def __str__(self):
        return f'Review for {self.listing.title} by {self.customer.get_full_name()}'

class ListingRating(TimeModel):

    listing = models.ForeignKey('listings.Listing', on_delete=models.CASCADE, related_name='ratings')
    rater = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_listing_ratings')
    rating = models.PositiveSmallIntegerField()
    review = models.ForeignKey(Review, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ('listing', 'rater')

class OwnerRating(TimeModel):

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owner_ratings')
    rater = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_owner_ratings')
    rating = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = ('owner', 'rater')