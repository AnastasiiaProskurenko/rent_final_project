from rest_framework.routers import DefaultRouter
from .views import SearchQueryViewSet, SearchHistoryViewSet, SearchViewSet
from django.urls import path, include

router = DefaultRouter()
router.register(r'search-queries', SearchQueryViewSet, basename='searchquery')
router.register(r'search-history', SearchHistoryViewSet, basename='searchhistory')
router.register(r'search', SearchViewSet, basename='search')

urlpatterns = [
    path('', include(router.urls)),
]

