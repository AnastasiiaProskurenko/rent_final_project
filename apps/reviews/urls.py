from rest_framework.routers import DefaultRouter
from .views import ReviewViewSet, ListingRatingViewSet, OwnerRatingViewSet
from django.urls import path, include

router = DefaultRouter()
router.register(r'reviews', ReviewViewSet, basename='review')
router.register(r'listing-ratings', ListingRatingViewSet, basename='listingrating')
router.register(r'owner-ratings', OwnerRatingViewSet, basename='ownerrating')

urlpatterns = [
    path('', include(router.urls)),
]

