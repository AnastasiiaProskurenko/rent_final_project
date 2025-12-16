

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ListingViewSet, ListingPhotoViewSet

app_name = 'listings'

router = DefaultRouter()
router.register(r'listings', ListingViewSet, basename='listing')
router.register(r'photos', ListingPhotoViewSet, basename='listing-photo')

urlpatterns = [
    path('', include(router.urls)),
]

"""
═══════════════════════════════════════════════════════════════════════════
                    ДОСТУПНІ URLS ДЛЯ LISTINGS (ОНОВЛЕНО)
═══════════════════════════════════════════════════════════════════════════

БАЗОВІ CRUD ОПЕРАЦІЇ:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GET     /api/listings/                          - Список оголошень
POST    /api/listings/                          - Створити оголошення
GET     /api/listings/{id}/                     - Деталі оголошення
PUT     /api/listings/{id}/                     - Оновити оголошення
PATCH   /api/listings/{id}/                     - Часткове оновлення
DELETE  /api/listings/{id}/                     - Видалити (м'яке)


СТАНДАРТНІ CUSTOM ACTIONS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GET     /api/listings/my_listings/              - Мої оголошення
GET     /api/listings/featured/                 - Виділені (популярні)
GET     /api/listings/popular/                  - З високим рейтингом
POST    /api/listings/{id}/activate/            - Активувати
POST    /api/listings/{id}/deactivate/          - Деактивувати
POST    /api/listings/{id}/upload_photos/       - Завантажити фото
DELETE  /api/listings/{id}/delete_photo/        - Видалити фото
GET     /api/listings/{id}/availability/        - Перевірка доступності


✅ НОВІ CUSTOM ACTIONS (для тварин та гостей):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GET     /api/listings/pet_friendly/             - Оголошення з тваринами
GET     /api/listings/for_large_groups/         - Для великих груп (10+ гостей)
GET     /api/listings/{id}/guest_capacity_info/ - Інфо про місткість


PHOTOS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GET     /api/photos/                            - Список фото
POST    /api/photos/                            - Завантажити фото
GET     /api/photos/{id}/                       - Деталі фото
DELETE  /api/photos/{id}/                       - Видалити фото
GET     /api/photos/?listing_id=123             - Фото конкретного оголошення


═══════════════════════════════════════════════════════════════════════════
                        ФІЛЬТРАЦІЯ (ОНОВЛЕНО)
═══════════════════════════════════════════════════════════════════════════

БАЗОВА ФІЛЬТРАЦІЯ:
──────────────────────────────────────────────────────────────────────────
GET /api/listings/?listing_type=apartment
GET /api/listings/?city=Kyiv
GET /api/listings/?country=Ukraine
GET /api/listings/?price__gte=100&price__lte=500
GET /api/listings/?num_rooms__gte=2
GET /api/listings/?max_guests__gte=10
GET /api/listings/?is_active=true


✅ НОВА ФІЛЬТРАЦІЯ (тварини):
──────────────────────────────────────────────────────────────────────────
GET /api/listings/?pets_allowed=true            - Тільки з тваринами
GET /api/listings/?pets_allowed=false           - Без тварин
GET /api/listings/?max_pets__gte=2              - Мінімум 2 тварини
GET /api/listings/?max_pets=0                   - Тварини заборонені


ЗРУЧНОСТІ:
──────────────────────────────────────────────────────────────────────────
GET /api/listings/?wifi=true
GET /api/listings/?kitchen=true
GET /api/listings/?free_parking=true
GET /api/listings/?air_conditioning=true


КОМБІНУВАННЯ:
──────────────────────────────────────────────────────────────────────────
GET /api/listings/?city=Kyiv&pets_allowed=true&max_guests__gte=10&price__lte=200


ПОШУК:
──────────────────────────────────────────────────────────────────────────
GET /api/listings/?search=apartment+kyiv
GET /api/listings/?search=pet+friendly


СОРТУВАННЯ:
──────────────────────────────────────────────────────────────────────────
GET /api/listings/?ordering=price              - За ціною (зростання)
GET /api/listings/?ordering=-price             - За ціною (спадання)
GET /api/listings/?ordering=max_guests         - За кількістю гостей
GET /api/listings/?ordering=-max_guests        - За кількістю (спадання)


═══════════════════════════════════════════════════════════════════════════
                        ПРИКЛАДИ ВИКОРИСТАННЯ
═══════════════════════════════════════════════════════════════════════════

1. ЗНАЙТИ ОГОЛОШЕННЯ З ТВАРИНАМИ:
   ──────────────────────────────────────────────────────────────────────
   GET /api/listings/pet_friendly/
   GET /api/listings/pet_friendly/?min_pets=2

   Response:
   [
       {
           "id": 1,
           "title": "Pet-Friendly Apartment",
           "pets_allowed": true,
           "max_pets": 3,
           "max_guests": 6,
           ...
       }
   ]


2. ЗНАЙТИ ДЛЯ ВЕЛИКОЇ ГРУПИ:
   ──────────────────────────────────────────────────────────────────────
   GET /api/listings/for_large_groups/
   GET /api/listings/for_large_groups/?min_guests=15

   Response:
   [
       {
           "id": 2,
           "title": "Large Villa",
           "num_rooms": 10,
           "max_guests": 20,
           ...
       }
   ]


3. ІНФОРМАЦІЯ ПРО МІСТКІСТЬ:
   ──────────────────────────────────────────────────────────────────────
   GET /api/listings/123/guest_capacity_info/

   Response:
   {
       "listing_id": 123,
       "num_rooms": 5,
       "max_guests_set": 10,
       "max_guests_calculated": 10,
       "rule": "2 guests per room",
       "is_at_capacity": true,
       "pets_allowed": true,
       "max_pets": 3,
       "available_bookings": 2
   }


4. ПЕРЕВІРКА ДОСТУПНОСТІ (ОНОВЛЕНО):
   ──────────────────────────────────────────────────────────────────────
   GET /api/listings/123/availability/?check_in=2025-12-01&check_out=2025-12-05

   Response:
   {
       "available": true,
       "check_in": "2025-12-01",
       "check_out": "2025-12-05",
       "listing_id": 123,
       "max_guests": 20,           // ✅ Максимум гостей
       "pets_allowed": true,       // ✅ Чи дозволені тварини
       "max_pets": 3              // ✅ Максимум тварин
   }


5. СТВОРИТИ ОГОЛОШЕННЯ (АВТОМАТИЧНИЙ РОЗРАХУНОК):
   ──────────────────────────────────────────────────────────────────────
   POST /api/listings/

   {
       "title": "Cozy 3-Bedroom Apartment",
       "city": "Kyiv",
       "country": "Ukraine",
       "num_rooms": 3,
       "price": 150.00,
       "pets_allowed": true,
       "max_pets": 2
       // max_guests не передано → розрахується автоматично = 9
   }

   Response:
   {
       "id": 1,
       "num_rooms": 3,
       "max_guests": 9,                    // ✅ Автоматично
       "recommended_max_guests": 9,
       "guests_per_room_rule": "3 guests per room (rooms: 3)",
       "pets_allowed": true,
       "max_pets": 2,
       ...
   }


6. КОМБІНОВАНИЙ ФІЛЬТР:
   ──────────────────────────────────────────────────────────────────────
   GET /api/listings/?city=Kyiv&pets_allowed=true&max_guests__gte=10&price__lte=300&ordering=-max_guests

   // Знайти в Києві з тваринами, мінімум 10 гостей, до 300 грн,
   // відсортувати за кількістю гостей (більше спочатку)


7. ФІЛЬТР ЗА КІЛЬКІСТЮ ТВАРИН:
   ──────────────────────────────────────────────────────────────────────
   GET /api/listings/?pets_allowed=true&max_pets__gte=3

   // Тварини дозволені, мінімум 3 тварини


═══════════════════════════════════════════════════════════════════════════
                        ЗМІНИ В RESPONSE
═══════════════════════════════════════════════════════════════════════════

РАНІШЕ (GET /api/listings/123/):
{
    "id": 123,
    "num_rooms": 5,
    "max_guests": 10,
    ...
}

✅ ТЕПЕР (GET /api/listings/123/):
{
    "id": 123,
    "num_rooms": 5,
    "max_guests": 10,
    "recommended_max_guests": 10,        // ✅ НОВЕ: розрахована кількість
    "guests_per_room_rule": "2 guests per room (rooms: 5)",  // ✅ НОВЕ
    "pets_allowed": true,                // ✅ НОВЕ
    "max_pets": 3,                       // ✅ НОВЕ
    ...
}


═══════════════════════════════════════════════════════════════════════════
"""
