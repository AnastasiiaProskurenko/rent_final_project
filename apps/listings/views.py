from rest_framework import viewsets, permissions
from .models import Listing, ListingPhoto
from .serializers import ListingSerializer, ListingPhotoSerializer
from .permissions import IsOwnerOrReadOnly
from apps.common.enums import Role


class ListingViewSet(viewsets.ModelViewSet):
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated:

            return Listing.objects.filter(is_active=True, is_deleted=False)

        if user.role in [Role.ADMIN, Role.SUPERADMIN]:

            return Listing.objects.all()
        elif user.role == Role.OWNER:

            return Listing.objects.filter(owner=user, is_deleted=False)
        else:

            return Listing.objects.filter(is_active=True, is_deleted=False)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class ListingPhotoViewSet(viewsets.ModelViewSet):
    queryset = ListingPhoto.objects.all()
    serializer_class = ListingPhotoSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]