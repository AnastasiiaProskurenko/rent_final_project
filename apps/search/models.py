from django.db import models
from apps.common.models import TimeModel
from django.contrib.auth import get_user_model

User = get_user_model()

class SearchQuery(TimeModel):

    query = models.CharField(max_length=255, db_index=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='search_queries')
    count = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('query', 'user')

class SearchHistory(TimeModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='search_history', null=True, blank=True)
    query = models.CharField(max_length=255)
    ip = models.CharField(max_length=50, blank=True, null=True)