from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from apps.users.views import EmailTokenObtainPairView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ============================================
    # HTML сторінки (✅ ДОДАТИ)
    # ============================================
    path('', include('apps.users.urls')),  # ✅ ДОДАТИ - HTML на /

    # ============================================
    # Admin
    # ============================================
    path('admin/', admin.site.urls),

    # ============================================
    # JWT Auth
    # ============================================
    path('api/auth/token/', EmailTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # ============================================
    # API Documentation
    # ============================================
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # ============================================
    # API endpoints
    # ============================================
    path('api/', include('apps.users.api_urls')),  # ✅ ЗМІНИТИ - API на /api/
    path('api/', include('apps.listings.urls')),
    path('api/', include('apps.bookings.urls')),
    path('api/', include('apps.reviews.urls')),
    path('api/', include('apps.notifications.urls')),
    path('api/', include('apps.payments.urls')),
    path('api/', include('apps.search.urls')),
    path('api/', include('apps.analytics.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
