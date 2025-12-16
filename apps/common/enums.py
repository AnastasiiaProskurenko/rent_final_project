from django.db import models


class PropertyType(models.TextChoices):
    """
    Типи нерухомості

    Використання в моделі:
        property_type = models.CharField(
            max_length=50,
            choices=PropertyType.choices,
            default=PropertyType.APARTMENT
        )

    Перевірка в коді:
        if listing.property_type == PropertyType.APARTMENT:
            print("Це квартира")

    Отримання label:
        label = PropertyType.APARTMENT.label  # "Квартира"

    Отримання всіх варіантів:
        choices = PropertyType.choices  # [('apartment', 'Квартира'), ...]
    """

    # ============================================
    # КВАРТИРИ
    # ============================================
    APARTMENT = 'apartment', 'Квартира'
    STUDIO = 'studio', 'Студія'
    PENTHOUSE = 'penthouse', 'Пентхаус'
    LOFT = 'loft', 'Лофт'
    DUPLEX = 'duplex', 'Дуплекс'

    # ============================================
    # БУДИНКИ
    # ============================================
    HOUSE = 'house', 'Будинок'
    VILLA = 'villa', 'Вілла'
    COTTAGE = 'cottage', 'Котедж'
    TOWNHOUSE = 'townhouse', 'Таунхаус'
    BUNGALOW = 'bungalow', 'Бунгало'
    MANSION = 'mansion', 'Особняк'

    # ============================================
    # ЗАМІСЬКІ
    # ============================================
    CABIN = 'cabin', 'Дача'
    CHALET = 'chalet', 'Шале'
    FARMHOUSE = 'farmhouse', 'Фермерський будинок'
    COUNTRY_HOUSE = 'country_house', 'Заміський будинок'

    # ============================================
    # КІМНАТИ
    # ============================================
    ROOM = 'room', 'Кімната'
    SHARED_ROOM = 'shared_room', 'Спільна кімната'
    HOSTEL = 'hostel', 'Хостел'

    # ============================================
    # СПЕЦІАЛЬНІ/УНІКАЛЬНІ
    # ============================================
    CASTLE = 'castle', 'Замок'
    BOAT = 'boat', 'Човен/Яхта'
    HOUSEBOAT = 'houseboat', 'Плавучий будинок'
    CAMPER = 'camper', 'Кемпер/RV'
    TENT = 'tent', 'Намет'
    TREEHOUSE = 'treehouse', 'Будиночок на дереві'
    IGLOO = 'igloo', 'Іглу'
    YURT = 'yurt', 'Юрта'
    LIGHTHOUSE = 'lighthouse', 'Маяк'

    # ============================================
    # ІНШЕ
    # ============================================
    OTHER = 'other', 'Інше'


class BookingStatus(models.TextChoices):


    PENDING = 'pending', 'Очікує підтвердження'
    CONFIRMED = 'confirmed', 'Підтверджено'
    CANCELLED = 'cancelled', 'Скасовано'
    COMPLETED = 'completed', 'Завершено'
    REJECTED = 'rejected', 'Відхилено'
    IN_PROGRESS = 'in_progress', 'В процесі'  # Гість вже заїхав
    EXPIRED = 'expired', 'Прострочено'  # Не підтверджено вчасно


class PaymentStatus(models.TextChoices):
    """Статуси платежу"""
    PENDING = 'pending', 'Pending'
    PROCESSING = 'processing', 'Processing'
    COMPLETED = 'completed', 'Completed'
    FAILED = 'failed', 'Failed'
    REFUNDED = 'refunded', 'Refunded'
    CANCELLED = 'cancelled', 'Cancelled'


class UserRole(models.TextChoices):
    """
    Ролі користувачів
    """

    CUSTOMER = 'customer', 'Клієнт'  # Орендар
    OWNER = 'owner', 'Власник'  # Власник нерухомості
    ADMIN = 'admin', 'Адміністратор'  # Адмін системи


class MessageStatus(models.TextChoices):
    """
    Статуси повідомлень
    """

    SENT = 'sent', 'Відправлено'
    DELIVERED = 'delivered', 'Доставлено'
    READ = 'read', 'Прочитано'
    FAILED = 'failed', 'Помилка відправки'


class NotificationType(models.TextChoices):
    """
    Типи сповіщень
    """

    # Бронювання
    BOOKING_REQUEST = 'booking_request', 'Новий запит на бронювання'
    BOOKING_CONFIRMED = 'booking_confirmed', 'Бронювання підтверджено'
    BOOKING_CANCELLED = 'booking_cancelled', 'Бронювання скасовано'
    BOOKING_REJECTED = 'booking_rejected', 'Бронювання відхилено'
    BOOKING_REMINDER = 'booking_reminder', 'Нагадування про бронювання'

    # Оплата
    PAYMENT_RECEIVED = 'payment_received', 'Оплата отримана'
    PAYMENT_FAILED = 'payment_failed', 'Помилка оплати'
    REFUND_PROCESSED = 'refund_processed', 'Повернення оброблено'

    # Відгуки
    REVIEW_RECEIVED = 'review_received', 'Новий відгук'
    REVIEW_RESPONSE = 'review_response', 'Відповідь на відгук'

    # Повідомлення
    MESSAGE_RECEIVED = 'message_received', 'Нове повідомлення'

    # Система
    ACCOUNT_VERIFIED = 'account_verified', 'Акаунт верифіковано'
    LISTING_APPROVED = 'listing_approved', 'Оголошення схвалено'
    LISTING_REJECTED = 'listing_rejected', 'Оголошення відхилено'

    # Інше
    REMINDER = 'reminder', 'Нагадування'
    PROMOTION = 'promotion', 'Акція'
    SYSTEM = 'system', 'Системне сповіщення'
    OTHER = 'other', 'Інше'


class CancellationPolicy(models.TextChoices):
    """
    Політики скасування бронювання

    Визначають умови повернення коштів при скасуванні
    """

    FLEXIBLE = 'flexible', 'Гнучка'
    # Повне повернення якщо скасовано за 24 години до заїзду

    MODERATE = 'moderate', 'Помірна'
    # Повне повернення якщо скасовано за 5 днів до заїзду

    STRICT = 'strict', 'Жорстка'
    # Повне повернення якщо скасовано за 7 днів до заїзду
    # 50% повернення якщо скасовано за 48 годин до заїзду

    SUPER_STRICT = 'super_strict', 'Дуже жорстка'
    # Повне повернення якщо скасовано за 30 днів до заїзду
    # 50% повернення якщо скасовано за 14 днів до заїзду

    NON_REFUNDABLE = 'non_refundable', 'Без повернення'
    # Без повернення коштів при скасуванні


class PaymentMethod(models.TextChoices):
    """
    Методи оплати
    """

    CARD = 'card', 'Credit/Debit Card'
    PAYPAL = 'paypal', 'PayPal'
    BANK_TRANSFER = 'bank_transfer', 'Bank Transfer'
    CASH = 'cash', 'Cash'
    CRYPTO = 'crypto', 'Cryptocurrency'


class Currency(models.TextChoices):
    """
    Валюти
    """

    UAH = 'UAH', 'Гривня (₴)'
    USD = 'USD', 'Долар ($)'
    EUR = 'EUR', 'Євро (€)'
    GBP = 'GBP', 'Фунт (£)'
    PLN = 'PLN', 'Злотий (zł)'


class Language(models.TextChoices):
    """
    Мови інтерфейсу
    """

    UK = 'uk', 'Українська'
    EN = 'en', 'English'
    RU = 'ru', 'Русский'
    PL = 'pl', 'Polski'


# ============================================
# ПРИКЛАДИ ВИКОРИСТАННЯ
# ============================================

"""
1. У МОДЕЛІ:
   ──────────────────────────────────────────────────────────────────────
   from apps.common.enums import PropertyType, BookingStatus

   class Listing(models.Model):
       property_type = models.CharField(
           max_length=50,
           choices=PropertyType.choices,
           default=PropertyType.APARTMENT,
           verbose_name='Property Type'
       )

   class Booking(models.Model):
       status = models.CharField(
           max_length=20,
           choices=BookingStatus.choices,
           default=BookingStatus.PENDING,
           verbose_name='Status'
       )


2. У VIEWS/SERIALIZERS:
   ──────────────────────────────────────────────────────────────────────
   from apps.common.enums import BookingStatus

   # Перевірка статусу
   if booking.status == BookingStatus.PENDING:
       # Логіка для очікуючих бронювань
       pass

   # Зміна статусу
   booking.status = BookingStatus.CONFIRMED
   booking.save()

   # Фільтрація
   confirmed_bookings = Booking.objects.filter(
       status=BookingStatus.CONFIRMED
   )


3. У SERIALIZERS - ВИБІР:
   ──────────────────────────────────────────────────────────────────────
   class ListingSerializer(serializers.ModelSerializer):
       property_type = serializers.ChoiceField(
           choices=PropertyType.choices,
           default=PropertyType.APARTMENT
       )


4. ОТРИМАННЯ LABEL:
   ──────────────────────────────────────────────────────────────────────
   listing = Listing.objects.get(id=1)

   # Отримати значення
   value = listing.property_type  # 'apartment'

   # Отримати label (назву)
   label = listing.get_property_type_display()  # 'Квартира'

   # Або через enum
   label = PropertyType.APARTMENT.label  # 'Квартира'


5. ВСІ ВАРІАНТИ ВИБОРУ:
   ──────────────────────────────────────────────────────────────────────
   # Список всіх choices
   all_choices = PropertyType.choices
   # [('apartment', 'Квартира'), ('house', 'Будинок'), ...]

   # Список всіх values
   all_values = PropertyType.values
   # ['apartment', 'house', 'villa', ...]

   # Список всіх labels
   all_labels = PropertyType.labels
   # ['Квартира', 'Будинок', 'Вілла', ...]


6. ПЕРЕВІРКА ЗНАЧЕННЯ:
   ──────────────────────────────────────────────────────────────────────
   # Перевірка чи значення в enum
   if 'apartment' in PropertyType.values:
       print("Apartment is valid property type")

   # Перевірка чи об'єкт має конкретне значення
   if listing.property_type == PropertyType.APARTMENT:
       print("This is an apartment")


7. У ФІЛЬТРАХ API:
   ──────────────────────────────────────────────────────────────────────
   GET /api/listings/?property_type=apartment
   GET /api/bookings/?status=confirmed

   # У ViewSet
   filterset_fields = {
       'property_type': ['exact', 'in'],
       'status': ['exact', 'in'],
   }


8. У ADMIN:
   ──────────────────────────────────────────────────────────────────────
   from apps.common.enums import PropertyType, BookingStatus

   class ListingAdmin(admin.ModelAdmin):
       list_filter = ['property_type', 'is_active']

       def get_queryset(self, request):
           qs = super().get_queryset(request)
           # Фільтр тільки квартир і будинків
           return qs.filter(
               property_type__in=[PropertyType.APARTMENT, PropertyType.HOUSE]
           )


9. ВАЛІДАЦІЯ У SERIALIZER:
   ──────────────────────────────────────────────────────────────────────
   from apps.common.enums import BookingStatus

   def validate_status(self, value):
       # Заборонено напряму встановлювати COMPLETED
       if value == BookingStatus.COMPLETED:
           raise serializers.ValidationError(
               'Cannot manually set status to COMPLETED'
           )
       return value


10. PERMISSION CHECKS:
    ──────────────────────────────────────────────────────────────────────
    from apps.common.enums import UserRole

    if request.user.role == UserRole.OWNER:
        # Логіка для власників
        pass
    elif request.user.role == UserRole.CUSTOMER:
        # Логіка для клієнтів
        pass


11. MIGRATION:
    ──────────────────────────────────────────────────────────────────────
    # В міграції Django автоматично створить правильні choices

    migrations.AddField(
        model_name='listing',
        name='property_type',
        field=models.CharField(
            choices=[
                ('apartment', 'Квартира'),
                ('house', 'Будинок'),
                ...
            ],
            default='apartment',
            max_length=50
        ),
    )
"""


# ============================================
# ДОПОМІЖНІ ФУНКЦІЇ
# ============================================

def get_enum_choices_dict(enum_class):
    """
    Повертає словник {value: label} для enum

    Usage:
        choices_dict = get_enum_choices_dict(PropertyType)
        # {'apartment': 'Квартира', 'house': 'Будинок', ...}
    """
    return {choice[0]: choice[1] for choice in enum_class.choices}


def is_valid_enum_value(enum_class, value):
    """
    Перевіряє чи значення є валідним для enum

    Usage:
        if is_valid_enum_value(PropertyType, 'apartment'):
            print("Valid")
    """
    return value in enum_class.values


# ============================================
# ДЛЯ FRONTEND
# ============================================

"""
Якщо потрібно передати choices на frontend:

# У ViewSet або APIView
from apps.common.enums import PropertyType

@action(detail=False, methods=['get'])
def property_types(self, request):
    '''Отримати всі типи нерухомості'''
    return Response({
        'property_types': [
            {'value': choice[0], 'label': choice[1]}
            for choice in PropertyType.choices
        ]
    })

# Response:
{
    "property_types": [
        {"value": "apartment", "label": "Квартира"},
        {"value": "house", "label": "Будинок"},
        ...
    ]
}

# Frontend може використати це для <select> або radio buttons
"""
