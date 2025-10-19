from rest_framework.routers import DefaultRouter
from .views import ListingViewViewSet
from django.urls import path, include

router = DefaultRouter()
router.register(r'listing-views', ListingViewViewSet, basename='listingview')

urlpatterns = [
    path('', include(router.urls)),
]

