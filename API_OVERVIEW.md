# API Overview

Нижче наведено стислий огляд доступних REST API ендпоінтів проєкту. Базовий префікс для всіх API: `/api/`.

## Автентифікація та документація
- `POST /api/auth/token/` – отримати JWT токен за email та паролем.
- `POST /api/auth/token/refresh/` – оновити access токен.
- `GET /api/schema/` – OpenAPI схема.
- `GET /api/schema/swagger-ui/` – інтерактивна Swagger-документація.

## Користувачі
- `users/` – CRUD для користувачів (автентифіковані користувачі, видимість залежить від ролі).
- `profiles/` – CRUD для профілів користувачів (читання для всіх, зміни для автентифікованих).

## Оголошення та фото
- `listings/` – стандартний CRUD для оголошень.
  - Додаткові дії: `my_listings/`, `featured/`, `popular/`, `pet_friendly/`, `for_large_groups/` та `guest_capacity_info/` і `availability/` для конкретного оголошення.
  - Керування статусом: `activate/`, `deactivate/`.
  - Фото: `upload_photos/`, `delete_photo/`.
- `photos/` – CRUD для фото оголошень і фільтрація за `listing_id`.

## Бронювання
- `bookings/` – CRUD для бронювань з додатковими фільтрами (`my_bookings/`, `my_listing_bookings/`, `upcoming/`, `past/`, `current/`, `pending/`).
  - Статусні дії: `approve/`, `reject/`, `cancel/`, `complete/`.
  - Інші дії: `statistics/`, `can_review/`.
- `calendar/` – читання бронювань у форматі календаря; `by_listing/` для конкретного оголошення.

## Відгуки
- `reviews/` – CRUD для відгуків та відповіді власника (`respond/`, `remove_response/`).
- Додаткові: `reviews/my/`, `listings/<id>/reviews/`, `listings/<id>/rating/`, `listings/top-rated/`.
- Рейтинги власників: `owners/<id>/rating/`, `owners/top-rated/`.

## Сповіщення
- `notifications/` – CRUD для сповіщень користувачів.

## Платежі
- `payments/` – CRUD для платежів.
- `refunds/` – CRUD для повернень.

## Пошук
- `search/` – пошукові запити по оголошеннях.
- `search-queries/` – робота з шаблонами пошукових запитів.
- `search-history/` – історія пошуку користувача.

## Аналітика
- `listing-views/` – аналітика переглядів оголошень.
