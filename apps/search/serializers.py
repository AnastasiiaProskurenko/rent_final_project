from rest_framework import serializers
from .models import SearchHistory

# Якщо там використовується SearchQuery - додайте:
SearchQuery = SearchHistory  # Alias


class SearchHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchHistory
        fields = '__all__'


class SearchQuerySerializer(serializers.Serializer):
    query = serializers.CharField(required=False, allow_blank=True)


class SearchSerializer(serializers.Serializer):
    query = serializers.CharField(required=False, allow_blank=True)
    min_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    max_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    city = serializers.CharField(required=False, allow_blank=True)
    rooms = serializers.IntegerField(required=False)
    property_type = serializers.CharField(required=False, allow_blank=True)