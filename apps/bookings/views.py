from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Booking
from .serializers import BookingSerializer, BookingCreateSerializer
from .filters import BookingFilter
from apps.common.enums import Role


class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = BookingFilter
    search_fields = ['listing__title', 'notes']
    ordering_fields = ['created_at', 'check_in', 'check_out', 'total_price']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return BookingCreateSerializer
        return BookingSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role in [Role.ADMIN, Role.SUPERADMIN]:
            return Booking.objects.select_related('customer', 'listing', 'created_by')
        elif user.role == Role.OWNER:
            return Booking.objects.filter(listing__owner=user)
        else:
            return Booking.objects.filter(customer=user)

    def perform_create(self, serializer):
        serializer.save(customer=self.request.user, created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):

        booking = self.get_object()
        if request.user != booking.listing.owner:
            return Response(
                {'error': 'Only the listing owner can confirm bookings.'},
                status=status.HTTP_403_FORBIDDEN
            )

        booking.status = 'agreed'
        booking.save()
        return Response({'status': 'Booking confirmed'})

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):

        booking = self.get_object()
        if request.user not in [booking.customer, booking.listing.owner]:
            return Response(
                {'error': 'Only the customer or listing owner can cancel bookings.'},
                status=status.HTTP_403_FORBIDDEN
            )

        booking.status = 'canceled'
        booking.save()
        return Response({'status': 'Booking canceled'})

    @action(detail=False, methods=['get'])
    def my_bookings(self, request):

        bookings = self.get_queryset().filter(customer=request.user)
        serializer = self.get_serializer(bookings, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_listing_bookings(self, request):

        if request.user.role not in [Role.OWNER, Role.ADMIN, Role.SUPERADMIN]:
            return Response(
                {'error': 'Only owners can view listing bookings.'},
                status=status.HTTP_403_FORBIDDEN
            )

        bookings = self.get_queryset().filter(listing__owner=request.user)
        serializer = self.get_serializer(bookings, many=True)
        return Response(serializer.data)