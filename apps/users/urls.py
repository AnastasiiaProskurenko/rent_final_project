from rest_framework.routers import DefaultRouter
from .views import UserViewSet, UserProfileViewSet
from django.urls import path, include

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'user-profiles', UserProfileViewSet, basename='userprofile')

urlpatterns = [
    path('', include(router.urls)),
]