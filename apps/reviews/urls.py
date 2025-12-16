from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ReviewViewSet,
    ListingReviewsView,
    ListingRatingView,
    OwnerRatingView,
    MyReviewsView,
    TopRatedListingsView,
    TopRatedOwnersView,
)

app_name = 'reviews'

# Router для ViewSet
router = DefaultRouter()
router.register(r'reviews', ReviewViewSet, basename='review')

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),

    # Додаткові endpoints
    path('reviews/my/', MyReviewsView.as_view(), name='my-reviews'),
    path('listings/<int:listing_id>/reviews/', ListingReviewsView.as_view(), name='listing-reviews'),
    path('listings/<int:listing_id>/rating/', ListingRatingView.as_view(), name='listing-rating'),
    path('listings/top-rated/', TopRatedListingsView.as_view(), name='top-rated-listings'),

    # Owner ratings
    path('owners/<int:owner_id>/rating/', OwnerRatingView.as_view(), name='owner-rating'),
    path('owners/top-rated/', TopRatedOwnersView.as_view(), name='top-rated-owners'),
]

# ════════════════════════════════════════════════════════════════════
# СТРУКТУРА URLs
# ════════════════════════════════════════════════════════════════════

"""
REVIEWS ENDPOINTS:
──────────────────────────────────────────────────────────────────────

ReviewViewSet (через router):
    GET    /api/reviews/                        - Список своїх відгуків
    POST   /api/reviews/                        - Створити відгук
    GET    /api/reviews/{id}/                   - Деталі відгуку
    PATCH  /api/reviews/{id}/                   - Оновити відгук
    DELETE /api/reviews/{id}/                   - Видалити відгук

    POST   /api/reviews/{id}/respond/           - Відповісти на відгук (власник)
    DELETE /api/reviews/{id}/remove_response/   - Видалити відповідь

Додаткові endpoints:
    GET /api/reviews/my/                        - Мої відгуки

Listing endpoints:
    GET /api/listings/{id}/reviews/             - Відгуки оголошення
    GET /api/listings/{id}/rating/              - Рейтинг оголошення
    GET /api/listings/top-rated/                - Топ оголошень

Owner endpoints:
    GET /api/owners/{id}/rating/                - Рейтинг власника
    GET /api/owners/top-rated/                  - Топ власників


ПРИКЛАДИ ЗАПИТІВ:
──────────────────────────────────────────────────────────────────────

1. Створити відгук:
   POST /api/reviews/
   {
       "booking_id": 1,
       "rating": 5,
       "comment": "Amazing place!"
   }

2. Отримати відгуки оголошення:
   GET /api/listings/1/reviews/?sort=newest&rating=5

3. Отримати рейтинг оголошення:
   GET /api/listings/1/rating/

4. Отримати рейтинг власника:
   GET /api/owners/5/rating/

5. Відповісти на відгук (власник):
   POST /api/reviews/1/respond/
   {
       "owner_response": "Thank you!"
   }

6. Мої відгуки:
   GET /api/reviews/my/

7. Топ оголошень:
   GET /api/listings/top-rated/?limit=10

8. Топ власників:
   GET /api/owners/top-rated/?limit=10
"""
