from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BookingViewSet, BookingCalendarViewSet

app_name = 'bookings'

# Router для ViewSets
router = DefaultRouter()
router.register(r'bookings', BookingViewSet, basename='booking')
router.register(r'calendar', BookingCalendarViewSet, basename='booking-calendar')

urlpatterns = [
    path('', include(router.urls)),
]

"""
═══════════════════════════════════════════════════════════════════════════
                        ДОСТУПНІ URLS ДЛЯ BOOKINGS
═══════════════════════════════════════════════════════════════════════════

БАЗОВІ CRUD ОПЕРАЦІЇ:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GET     /api/bookings/                          - Список бронювань
POST    /api/bookings/                          - Створити бронювання
GET     /api/bookings/{id}/                     - Деталі бронювання
PUT     /api/bookings/{id}/                     - Оновити бронювання
PATCH   /api/bookings/{id}/                     - Часткове оновлення
DELETE  /api/bookings/{id}/                     - Видалити бронювання


ФІЛЬТРИ СПИСКУ:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GET     /api/bookings/my_bookings/              - Мої бронювання (як клієнт)
GET     /api/bookings/my_listing_bookings/      - Бронювання моїх оголошень (як owner)
GET     /api/bookings/upcoming/                 - Майбутні бронювання
GET     /api/bookings/past/                     - Минулі бронювання
GET     /api/bookings/current/                  - Поточні (зараз активні)
GET     /api/bookings/pending/                  - Що очікують підтвердження


ЗМІНА СТАТУСУ:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
POST    /api/bookings/{id}/approve/             - Підтвердити (owner/admin)
POST    /api/bookings/{id}/reject/              - Відхилити (owner/admin)
POST    /api/bookings/{id}/cancel/              - Скасувати (customer/owner/admin)
POST    /api/bookings/{id}/complete/            - Завершити (owner/admin)


СТАТИСТИКА ТА ДОДАТКОВО:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GET     /api/bookings/statistics/               - Статистика бронювань
GET     /api/bookings/{id}/can_review/          - Чи можна залишити відгук


КАЛЕНДАР (read-only):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GET     /api/calendar/                          - Всі бронювання для календаря
GET     /api/calendar/by_listing/               - Бронювання конкретного оголошення


═══════════════════════════════════════════════════════════════════════════
                        ПРИКЛАДИ ЗАПИТІВ
═══════════════════════════════════════════════════════════════════════════

1. СТВОРИТИ БРОНЮВАННЯ:
   ────────────────────────────────────────────────────────────────────────
   POST /api/bookings/

   Request Body:
   {
       "listing": 10,
       "check_in": "2025-12-01",
       "check_out": "2025-12-05",
       "num_guests": 2,
       "notes": "Early check-in please"
   }

   Response: (використовує BookingSerializer)
   {
       "id": 1,
       "customer": 5,
       "customer_name": "John Doe",
       "customer_email": "john@example.com",
       "listing": 10,
       "listing_title": "Cozy Apartment",
       "check_in": "2025-12-01",
       "check_out": "2025-12-05",
       "num_guests": 2,
       "num_nights": 4,
       "total_price": "400.00",
       "status": "waiting",
       "status_display": "Waiting",
       ...
   }


2. МОЇ БРОНЮВАННЯ:
   ────────────────────────────────────────────────────────────────────────
   GET /api/bookings/my_bookings/
   Authorization: Bearer <token>


3. ПІДТВЕРДИТИ БРОНЮВАННЯ:
   ────────────────────────────────────────────────────────────────────────
   POST /api/bookings/123/approve/
   Authorization: Bearer <token>

   Response:
   {
       "id": 123,
       "status": "agreed",
       "status_display": "Agreed",
       ...
   }


4. СКАСУВАТИ З ПРИЧИНОЮ:
   ────────────────────────────────────────────────────────────────────────
   POST /api/bookings/123/cancel/
   Authorization: Bearer <token>

   Request Body:
   {
       "reason": "Change of plans"
   }


5. СТАТИСТИКА:
   ────────────────────────────────────────────────────────────────────────
   GET /api/bookings/statistics/
   Authorization: Bearer <token>

   Response:
   {
       "total": 45,
       "by_status": {
           "waiting": 5,
           "agreed": 10,
           "rejected": 3,
           "canceled": 7,
           "completed": 20
       },
       "by_time": {
           "upcoming": 8,
           "current": 2,
           "past": 35
       },
       "total_revenue": 15000.00
   }


6. КАЛЕНДАР ДЛЯ ОГОЛОШЕННЯ:
   ────────────────────────────────────────────────────────────────────────
   GET /api/calendar/by_listing/?listing_id=10

   Response:
   [
       {
           "id": 1,
           "start": "2025-12-01",
           "end": "2025-12-05",
           "status": "agreed",
           "customer_name": "John Doe"
       },
       {
           "id": 2,
           "start": "2025-12-10",
           "end": "2025-12-15",
           "status": "waiting",
           "customer_name": "Jane Smith"
       }
   ]


═══════════════════════════════════════════════════════════════════════════
                        ФІЛЬТРАЦІЯ ТА ПОШУК
═══════════════════════════════════════════════════════════════════════════

ФІЛЬТРАЦІЯ:
───────────────────────────────────────────────────────────────────────────
GET /api/bookings/?status=waiting
GET /api/bookings/?status__in=waiting,agreed
GET /api/bookings/?listing=10
GET /api/bookings/?customer=5
GET /api/bookings/?check_in__gte=2025-12-01
GET /api/bookings/?check_out__lte=2025-12-31
GET /api/bookings/?total_price__gte=100&total_price__lte=500
GET /api/bookings/?num_guests__gte=2


ПОШУК:
───────────────────────────────────────────────────────────────────────────
GET /api/bookings/?search=john
GET /api/bookings/?search=apartment+kyiv


СОРТУВАННЯ:
───────────────────────────────────────────────────────────────────────────
GET /api/bookings/?ordering=check_in              - За датою заїзду (зростання)
GET /api/bookings/?ordering=-check_in             - За датою заїзду (спадання)
GET /api/bookings/?ordering=total_price           - За ціною
GET /api/bookings/?ordering=-created_at           - За датою створення (нові)


КОМБІНУВАННЯ:
───────────────────────────────────────────────────────────────────────────
GET /api/bookings/?status=agreed&check_in__gte=2025-12-01&ordering=check_in


═══════════════════════════════════════════════════════════════════════════
                        ПРАВА ДОСТУПУ
═══════════════════════════════════════════════════════════════════════════

ДОЗВОЛЕНО ДЛЯ ВСІХ АВТОРИЗОВАНИХ:
- list, retrieve, create

ДОЗВОЛЕНО ДЛЯ CUSTOMER АБО LISTING.OWNER АБО ADMIN:
- update, partial_update, destroy, cancel

ДОЗВОЛЕНО ТІЛЬКИ ДЛЯ LISTING.OWNER АБО ADMIN:
- approve, reject, complete, pending

ДОЗВОЛЕНО ТІЛЬКИ ДЛЯ OWNER АБО ADMIN:
- my_listing_bookings


═══════════════════════════════════════════════════════════════════════════
                        СЕРІАЛІЗАТОРИ ПО ACTIONS
═══════════════════════════════════════════════════════════════════════════

list                    → BookingListSerializer
retrieve                → BookingSerializer
create                  → BookingCreateSerializer (response: BookingSerializer)
update/partial_update   → BookingUpdateSerializer (response: BookingSerializer)
approve/reject/cancel   → BookingStatusUpdateSerializer (response: BookingSerializer)


═══════════════════════════════════════════════════════════════════════════
"""
