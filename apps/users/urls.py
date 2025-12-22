from django.urls import path
from .views import welcome_view, login_view, register_view, logout_view

# HTML сторінки
urlpatterns = [
    path('', welcome_view, name='welcome'),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),
]