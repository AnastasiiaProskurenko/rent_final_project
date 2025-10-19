from django.db import models
from apps.common.models import TimeModel
from django.contrib.auth import get_user_model

User = get_user_model()

class ListingView(TimeModel):
#історія запитів
    listing = models.ForeignKey('listings.Listing', on_delete=models.CASCADE, related_name='views')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip = models.CharField(max_length=50, blank=True, null=True)
    user_agent = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['listing']),
            models.Index(fields=['user']),
        ]