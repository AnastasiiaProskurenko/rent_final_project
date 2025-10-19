from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Payment, Refund
from .serializers import PaymentSerializer, RefundSerializer
from apps.common.enums import Role


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['method', 'status', 'user']
    search_fields = ['transaction_id']
    ordering_fields = ['created_at', 'amount']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user

        if user.role in [Role.ADMIN, Role.SUPERADMIN]:

            return Payment.objects.select_related('user', 'booking')
        elif user.role == Role.OWNER:

            return Payment.objects.filter(
                booking__listing__owner=user
            ).select_related('user', 'booking')
        else:

            return Payment.objects.filter(user=user).select_related('user', 'booking')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def process_payment(self, request, pk=None):
        """Process a payment (simulate payment processing)"""
        payment = self.get_object()
        if payment.status != 'pending':
            return Response(
                {'error': 'Only pending payments can be processed.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Simulate payment processing
        payment.status = 'completed'
        payment.transaction_id = f"txn_{payment.id}_{request.user.id}"
        payment.save()

        return Response({'status': 'Payment processed successfully'})

    @action(detail=False, methods=['get'])
    def my_payments(self, request):
        """Get current user's payments"""
        payments = self.get_queryset().filter(user=request.user)
        serializer = self.get_serializer(payments, many=True)
        return Response(serializer.data)


class RefundViewSet(viewsets.ModelViewSet):
    queryset = Refund.objects.all()
    serializer_class = RefundSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'payment']
    search_fields = ['reason']
    ordering_fields = ['created_at', 'amount']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user

        if user.role in [Role.ADMIN, Role.SUPERADMIN]:
            # Адмін бачить все
            return Refund.objects.select_related('payment', 'processed_by')
        elif user.role == Role.OWNER:
            # Власник бачить refunds за своїми оголошеннями
            return Refund.objects.filter(
                payment__booking__listing__owner=user
            ).select_related('payment', 'processed_by')
        else:
            # Customer бачить тільки свої refunds
            return Refund.objects.filter(
                payment__user=user
            ).select_related('payment', 'processed_by')

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a refund (for admins)"""
        if request.user.role not in [Role.ADMIN, Role.SUPERADMIN]:
            return Response(
                {'error': 'Only admins can approve refunds.'},
                status=status.HTTP_403_FORBIDDEN
            )

        refund = self.get_object()
        if refund.status != 'pending':
            return Response(
                {'error': 'Only pending refunds can be approved.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        refund.status = 'approved'
        refund.processed_by = request.user
        refund.save()

        return Response({'status': 'Refund approved'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a refund (for admins)"""
        if request.user.role not in [Role.ADMIN, Role.SUPERADMIN]:
            return Response(
                {'error': 'Only admins can reject refunds.'},
                status=status.HTTP_403_FORBIDDEN
            )

        refund = self.get_object()
        if refund.status != 'pending':
            return Response(
                {'error': 'Only pending refunds can be rejected.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        refund.status = 'rejected'
        refund.processed_by = request.user
        refund.save()

        return Response({'status': 'Refund rejected'})