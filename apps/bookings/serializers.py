from rest_framework import serializers
from .models import Booking
from apps.listings.models import Listing, ListingPhoto
from apps.listings.serializers import LocationSerializer as ListingLocationSerializer


class ListingSerializer(serializers.ModelSerializer):
    """Мінімальна інформація про оголошення для бронювання"""

    main_photo = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()

    class Meta:
        model = Listing
        fields = [
            'id',
            'title',
            'property_type',
            'city',
            'address',
            'price',
            'main_photo'
        ]

    def get_main_photo(self, obj):
        photo = obj.photos.filter(is_main=True).first()
        if photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(photo.image.url)
        return None

    def get_city(self, obj):
        return obj.location.city if obj.location else None

    def get_address(self, obj):
        return obj.location.address if obj.location else None


class BookingSerializer(serializers.ModelSerializer):
    """Serializer для перегляду бронювань"""

    listing = ListingSerializer(read_only=True)
    location = ListingLocationSerializer(read_only=True)
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    customer_email = serializers.CharField(source='customer.email', read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id',
            'listing',
            'location',
            'customer',
            'customer_name',
            'customer_email',
            'check_in',
            'check_out',
            'num_guests',
            'total_price',
            'status',
            'cancellation_reason',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['customer', 'location', 'total_price', 'created_at', 'updated_at']


class BookingListSerializer(serializers.ModelSerializer):
    """Serializer для списку бронювань (коротка інформація)"""

    listing_title = serializers.CharField(source='listing.title', read_only=True)
    listing_city = serializers.SerializerMethodField()
    location = ListingLocationSerializer(read_only=True)
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id',
            'listing_title',
            'listing_city',
            'location',
            'customer_name',
            'check_in',
            'check_out',
            'num_guests',
            'total_price',
            'status',
            'created_at'
        ]

    def get_listing_city(self, obj):
        return obj.location.city if obj.location else None


class BookingCreateSerializer(serializers.ModelSerializer):
    """Serializer для створення бронювання"""

    class Meta:
        model = Booking
        fields = [
            'listing',
            'check_in',
            'check_out',
            'num_guests'
        ]

    def validate(self, data):
        """Валідація дат та доступності"""
        check_in = data.get('check_in')
        check_out = data.get('check_out')
        listing = data.get('listing')

        # Перевірка що check_out після check_in
        if check_out <= check_in:
            raise serializers.ValidationError(
                "Дата виїзду повинна бути пізніше дати заїзду"
            )

        # Перевірка кількості гостей
        num_guests = data.get('num_guests', 1)
        if num_guests > listing.max_guests:
            raise serializers.ValidationError(
                f"Максимальна кількість гостей: {listing.max_guests}"
            )

        # Перевірка що оголошення активне
        if not listing.is_active or listing.is_deleted:
            raise serializers.ValidationError(
                "Це оголошення недоступне для бронювання"
            )

        # Перевірка що дати не зайняті
        overlapping = Booking.objects.filter(
            listing=listing,
            status__in=['PENDING', 'CONFIRMED'],
            check_in__lt=check_out,
            check_out__gt=check_in
        ).exists()

        if overlapping:
            raise serializers.ValidationError(
                "Ці дати вже заброньовані"
            )

        data['location'] = listing.location
        return data

    def create(self, validated_data):
        """Створення бронювання з розрахунком ціни"""
        listing = validated_data['listing']
        check_in = validated_data['check_in']
        check_out = validated_data['check_out']

        # Розрахунок кількості днів та загальної ціни
        num_days = (check_out - check_in).days
        total_price = listing.price * num_days

        # Створюємо бронювання
        booking = Booking.objects.create(
            customer=self.context['request'].user,
            location=listing.location,
            total_price=total_price,
            **validated_data
        )

        return booking


class BookingUpdateSerializer(serializers.ModelSerializer):
    """Serializer для оновлення бронювання"""

    class Meta:
        model = Booking
        fields = [
            'status',
            'cancellation_reason'
        ]

    def validate_status(self, value):
        """Валідація зміни статусу"""
        booking = self.instance
        user = self.context['request'].user

        # Тільки власник оголошення може підтверджувати
        if value == 'CONFIRMED' and booking.listing.owner != user:
            raise serializers.ValidationError(
                "Тільки власник може підтверджувати бронювання"
            )

        # Тільки клієнт або власник можуть скасовувати
        if value == 'CANCELLED':
            if user not in [booking.customer, booking.listing.owner]:
                raise serializers.ValidationError(
                    "Ви не можете скасувати це бронювання"
                )

        return value


class BookingStatusUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer для зміни статусу бронювання
    Використовується для швидкої зміни тільки статусу
    """

    class Meta:
        model = Booking
        fields = ['status', 'cancellation_reason']
        extra_kwargs = {
            'cancellation_reason': {'required': False, 'allow_blank': True}
        }

    def validate(self, data):
        """Валідація зміни статусу"""
        booking = self.instance
        user = self.context['request'].user
        new_status = data.get('status')

        if not new_status:
            return data

        # Перевірка прав на зміну статусу
        if new_status == 'CONFIRMED':
            if booking.listing.owner != user:
                raise serializers.ValidationError({
                    'status': "Тільки власник оголошення може підтверджувати бронювання"
                })
            if booking.status != 'PENDING':
                raise serializers.ValidationError({
                    'status': "Можна підтвердити тільки бронювання зі статусом PENDING"
                })

        elif new_status == 'CANCELLED':
            if user not in [booking.customer, booking.listing.owner]:
                raise serializers.ValidationError({
                    'status': "Ви не можете скасувати це бронювання"
                })
            if booking.status == 'COMPLETED':
                raise serializers.ValidationError({
                    'status': "Не можна скасувати завершене бронювання"
                })
            if not data.get('cancellation_reason'):
                raise serializers.ValidationError({
                    'cancellation_reason': "Вкажіть причину скасування"
                })

        elif new_status == 'COMPLETED':
            if booking.listing.owner != user:
                raise serializers.ValidationError({
                    'status': "Тільки власник може відмічати бронювання як завершене"
                })
            if booking.status != 'CONFIRMED':
                raise serializers.ValidationError({
                    'status': "Можна завершити тільки підтверджене бронювання"
                })

        return data
