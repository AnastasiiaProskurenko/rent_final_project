from rest_framework.routers import DefaultRouter
from .views import ListingViewSet, ListingPhotoViewSet
from django.urls import path, include

router = DefaultRouter()
router.register(r'listings', ListingViewSet, basename='listing')
router.register(r'listing-photos', ListingPhotoViewSet, basename='listingphoto')

urlpatterns = [
    path('', include(router.urls)),
]