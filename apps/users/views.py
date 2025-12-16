from rest_framework import viewsets, permissions
from django.contrib.auth import get_user_model, login, authenticate
from django.shortcuts import render, redirect
from django.contrib.auth.forms import  AuthenticationForm
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import UserSerializer, UserProfileSerializer, EmailTokenObtainPairSerializer
from .models import UserProfile
from .forms import RegisterForm, EmailAuthenticationForm

User = get_user_model()


# ============================================
# API ViewSets (існуючий код)
# ============================================

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.DjangoModelPermissionsOrAnonReadOnly]


class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer


# ============================================
# HTML Views (ДОДАТИ)
# ============================================

# Початкова сторінка
def welcome_view(request):
    if request.user.is_authenticated:
        return redirect('/api/listings/')  # або твій URL після логіну
    return render(request, 'users/welcome.html')


# Реєстрація
def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('/api/listings/')
    else:
        form = RegisterForm()

    return render(request, 'users/register.html', {'form': form})


# Логін
def login_view(request):
    if request.user.is_authenticated:
        return redirect('/api/listings/')

    if request.method == 'POST':
        form = EmailAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('/api/listings/')
    else:
        form = EmailAuthenticationForm()

    return render(request, 'users/login.html', {'form': form})
