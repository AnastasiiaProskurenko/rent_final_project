from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q, Count
from django.utils import timezone

from .models import Booking
from .serializers import (
    BookingSerializer,
    BookingListSerializer,
    BookingCreateSerializer,
    BookingUpdateSerializer,
    BookingStatusUpdateSerializer
)
from .permissions import (
    IsCustomerOrListingOwnerOrAdmin,
    IsListingOwnerOrAdmin,
    IsCustomerRole,
)
from apps.common.enums import BookingStatus


class BookingViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управління бронюваннями

    list: GET /api/bookings/ - список бронювань
    retrieve: GET /api/bookings/{id}/ - деталі бронювання
    create: POST /api/bookings/ - створити бронювання
    update: PUT /api/bookings/{id}/ - оновити бронювання
    partial_update: PATCH /api/bookings/{id}/ - часткове оновлення
    destroy: DELETE /api/bookings/{id}/ - видалити бронювання
    """

    queryset = Booking.objects.select_related(
        'customer',
        'listing',
        'listing__owner',
        'listing__location',
        'location',

    ).all()

    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    # Фільтрація
    filterset_fields = {
        'status': ['exact', 'in'],
        'listing': ['exact'],
        'location': ['exact'],
        'customer': ['exact'],
        'check_in': ['gte', 'lte', 'exact'],
        'check_out': ['gte', 'lte', 'exact'],
        'num_guests': ['gte', 'lte', 'exact'],
        'total_price': ['gte', 'lte', 'exact'],
    }

    # Пошук
    search_fields = [
        'customer__email',
        'customer__first_name',
        'customer__last_name',
        'listing__title',
        'listing__location__city',
        'location__city',
        'location__address',
        'notes'
    ]

    # Сортування
    ordering_fields = [
        'created_at',
        'check_in',
        'check_out',
        'total_price',
        'status'
    ]
    ordering = ['-created_at']

    def get_serializer_class(self):
        """
        Вибір серіалізатора залежно від action
        """
        if self.action == 'list':
            return BookingListSerializer

        elif self.action == 'create':
            return BookingCreateSerializer

        elif self.action in ['update', 'partial_update']:
            return BookingUpdateSerializer

        elif self.action in ['approve', 'reject', 'cancel', 'complete']:
            return BookingStatusUpdateSerializer

        return BookingSerializer

    def get_queryset(self):
        """
        Фільтрація queryset залежно від прав користувача
        """
        user = self.request.user
        queryset = super().get_queryset()

        # Адміни бачать всі бронювання
        if user.is_admin():
            return queryset

        # Owners бачать бронювання своїх оголошень + свої бронювання як клієнт
        if user.is_owner():
            return queryset.filter(
                Q(listing__owner=user) | Q(customer=user)
            )

        # Клієнти бачать тільки свої бронювання
        return queryset.filter(customer=user)

    def get_permissions(self):
        """
        Права доступу залежно від action
        """
        if self.action == 'create':
            return [permissions.IsAuthenticated(), IsCustomerRole()]

        if self.action in ['update', 'partial_update', 'destroy']:
            return [
                permissions.IsAuthenticated(),
                IsCustomerOrListingOwnerOrAdmin()
            ]

        elif self.action in ['approve', 'reject', 'complete']:
            return [
                permissions.IsAuthenticated(),
                IsListingOwnerOrAdmin()
            ]

        elif self.action == 'cancel':
            return [
                permissions.IsAuthenticated(),
                IsCustomerOrListingOwnerOrAdmin()
            ]

        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        """
        При створенні автоматично встановлюємо customer та created_by
        """
        serializer.save(
            customer=self.request.user
        )

    def perform_destroy(self, instance):
        """
        Видалення бронювання (тільки якщо статус WAITING)
        """
        if instance.status != BookingStatus.PENDING:
            from rest_framework.exceptions import ValidationError
            raise ValidationError(
                "Can only delete bookings with 'waiting' status"
            )

        instance.delete()

    # ============================================
    # CUSTOM ACTIONS - ФІЛЬТРИ
    # ============================================

    @action(detail=False, methods=['get'])
    def my_bookings(self, request):
        """
        Мої бронювання (як клієнт)
        GET /api/bookings/my_bookings/
        """
        queryset = self.get_queryset().filter(customer=request.user)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = BookingListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = BookingListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_listing_bookings(self, request):
        """
        Бронювання моїх оголошень (як власник)
        GET /api/bookings/my_listing_bookings/
        """
        if not request.user.is_owner() and not request.user.is_admin():
            return Response(
                {'error': 'Only owners can view listing bookings'},
                status=status.HTTP_403_FORBIDDEN
            )

        queryset = self.get_queryset().filter(listing__owner=request.user)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = BookingListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = BookingListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """
        Майбутні бронювання
        GET /api/bookings/upcoming/
        """
        today = timezone.now().date()
        queryset = self.get_queryset().filter(
            check_in__gte=today,
            status__in=[BookingStatus.PENDING, BookingStatus.CONFIRMED]
        )

        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = BookingListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = BookingListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def past(self, request):
        """
        Минулі бронювання
        GET /api/bookings/past/
        """
        today = timezone.now().date()
        queryset = self.get_queryset().filter(check_out__lt=today)

        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = BookingListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = BookingListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def current(self, request):
        """
        Поточні бронювання (зараз відбуваються)
        GET /api/bookings/current/
        """
        today = timezone.now().date()
        queryset = self.get_queryset().filter(
            check_in__lte=today,
            check_out__gte=today,
            status=BookingStatus.CONFIRMED
        )

        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = BookingListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = BookingListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """
        Бронювання що очікують підтвердження
        GET /api/bookings/pending/
        Тільки для власників оголошень
        """
        if not request.user.is_owner() and not request.user.is_admin():
            return Response(
                {'error': 'Only owners can view pending bookings'},
                status=status.HTTP_403_FORBIDDEN
            )

        queryset = self.get_queryset().filter(
            listing__owner=request.user,
            status=BookingStatus.PENDING
        )

        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = BookingListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = BookingListSerializer(queryset, many=True)
        return Response(serializer.data)

    # ============================================
    # CUSTOM ACTIONS - ЗМІНА СТАТУСУ
    # ============================================

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Підтвердити бронювання
        POST /api/bookings/{id}/approve/
        Тільки для власника оголошення або адміна
        """
        booking = self.get_object()

        # Перевірка поточного статусу
        if booking.status != BookingStatus.PENDING:
            return Response(
                {'error': 'Can only approve bookings with "waiting" status'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Зміна статусу
        booking.status = BookingStatus.CONFIRMED
        booking.save()

        serializer = BookingSerializer(booking)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """
        Відхилити бронювання
        POST /api/bookings/{id}/reject/
        Body: {"reason": "..."} (optional)
        Тільки для власника оголошення або адміна
        """
        booking = self.get_object()

        # Перевірка поточного статусу
        if booking.status != BookingStatus.PENDING:
            return Response(
                {'error': 'Can only reject bookings with "waiting" status'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Отримуємо причину з request (опціонально)
        reason = request.data.get('reason', '')
        if reason:
            booking.notes = f"{booking.notes}\n\nRejection reason: {reason}".strip()

        # Зміна статусу
        booking.status = BookingStatus.REJECTED
        booking.save()

        serializer = BookingSerializer(booking)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Скасувати бронювання
        POST /api/bookings/{id}/cancel/
        Body: {"reason": "..."} (optional)
        Для клієнта або власника оголошення або адміна
        """
        booking = self.get_object()

        # Перевірка поточного статусу
        if booking.status in [BookingStatus.CANCELLED, BookingStatus.COMPLETED]:
            return Response(
                {'error': f'Cannot cancel booking with "{booking.status}" status'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Перевірка дати (не можна скасувати якщо вже почалось)
        today = timezone.now().date()
        if booking.check_in <= today:
            return Response(
                {'error': 'Cannot cancel booking that has already started'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Отримуємо причину з request (опціонально)
        reason = request.data.get('reason', '')
        if reason:
            booking.notes = f"{booking.notes}\n\nCancellation reason: {reason}".strip()

        # Зміна статусу
        booking.status = BookingStatus.CANCELLED
        booking.save()

        serializer = BookingSerializer(booking)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        Завершити бронювання
        POST /api/bookings/{id}/complete/
        Тільки для власника оголошення або адміна
        """
        booking = self.get_object()

        # Перевірка поточного статусу
        if booking.status != BookingStatus.CONFIRMED:
            return Response(
                {'error': 'Can only complete bookings with "agreed" status'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Перевірка дати (має закінчитись)
        today = timezone.now().date()
        if booking.check_out > today:
            return Response(
                {'error': 'Cannot complete booking before check-out date'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Зміна статусу
        booking.status = BookingStatus.COMPLETED
        booking.save()

        serializer = BookingSerializer(booking)
        return Response(serializer.data)

    # ============================================
    # CUSTOM ACTIONS - СТАТИСТИКА
    # ============================================

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Статистика бронювань
        GET /api/bookings/statistics/
        """
        queryset = self.get_queryset()

        # Якщо owner - статистика для його оголошень
        if request.user.is_owner() and not request.user.is_admin():
            queryset = queryset.filter(listing__owner=request.user)
        # Якщо customer - статистика його бронювань
        elif not request.user.is_admin():
            queryset = queryset.filter(customer=request.user)

        today = timezone.now().date()

        stats = {
            'total': queryset.count(),
            'by_status': {
                'waiting': queryset.filter(status=BookingStatus.PENDING).count(),
                'agreed': queryset.filter(status=BookingStatus.CONFIRMED).count(),
                'rejected': queryset.filter(status=BookingStatus.REJECTED).count(),
                'canceled': queryset.filter(status=BookingStatus.CANCELLED).count(),
                'completed': queryset.filter(status=BookingStatus.COMPLETED).count(),
            },
            'by_time': {
                'upcoming': queryset.filter(
                    check_in__gte=today,
                    status__in=[BookingStatus.PENDING, BookingStatus.CONFIRMED]
                ).count(),
                'current': queryset.filter(
                    check_in__lte=today,
                    check_out__gte=today,
                    status=BookingStatus.CONFIRMED
                ).count(),
                'past': queryset.filter(check_out__lt=today).count(),
            },
            'total_revenue': sum(
                booking.total_price for booking in queryset.filter(
                    status__in=[BookingStatus.CONFIRMED, BookingStatus.COMPLETED]
                )
            ),
        }

        return Response(stats)

    @action(detail=True, methods=['get'])
    def can_review(self, request, pk=None):
        """
        Перевірка чи може клієнт залишити відгук
        GET /api/bookings/{id}/can_review/
        """
        booking = self.get_object()

        # Тільки клієнт може перевіряти
        if request.user != booking.customer:
            return Response(
                {'error': 'Only customer can check review availability'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Можна залишити відгук якщо бронювання завершене
        can_review = (
                booking.status == BookingStatus.COMPLETED and
                booking.check_out < timezone.now().date()
        )

        # Перевірка чи вже є відгук
        has_review = hasattr(booking, 'review')

        return Response({
            'can_review': can_review and not has_review,
            'has_review': has_review,
            'booking_status': booking.status,
            'check_out': booking.check_out
        })


# ============================================
# ДОДАТКОВИЙ ViewSet для швидкого перегляду
# ============================================

class BookingCalendarViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для календаря бронювань
    Тільки для читання, показує зайняті дати
    """
    queryset = Booking.objects.filter(
        status__in=[BookingStatus.PENDING, BookingStatus.CONFIRMED]
    )
    serializer_class = BookingListSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @action(detail=False, methods=['get'])
    def by_listing(self, request):
        """
        Бронювання для конкретного оголошення (для календаря)
        GET /api/bookings/calendar/by_listing/?listing_id=123
        """
        listing_id = request.query_params.get('listing_id')

        if not listing_id:
            return Response(
                {'error': 'listing_id parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        bookings = self.queryset.filter(listing_id=listing_id)

        # Форматування для календаря
        calendar_data = []
        for booking in bookings:
            calendar_data.append({
                'id': booking.id,
                'start': booking.check_in,
                'end': booking.check_out,
                'status': booking.status,
                'customer_name': booking.customer.get_full_name(),
            })

        return Response(calendar_data)
