from rest_framework import serializers
from .models import SearchQuery, SearchHistory
from apps.users.serializers import UserSerializer


class SearchQuerySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = SearchQuery
        fields = '__all__'
        read_only_fields = ('count', 'created_at', 'updated_at')


class SearchHistorySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = SearchHistory
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class SearchSerializer(serializers.Serializer):
    query = serializers.CharField(max_length=255)
    filters = serializers.JSONField(required=False, default=dict)
    
    def validate_query(self, value):
        if not value.strip():
            raise serializers.ValidationError("Search query cannot be empty.")
        return value.strip()

