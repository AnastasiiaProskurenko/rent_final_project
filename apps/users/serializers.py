from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import AuthenticationFailed


User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User

        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'is_active')


try:
    from .models import UserProfile
    class UserProfileSerializer(serializers.ModelSerializer):
        class Meta:
            model = UserProfile
            fields = ('id', 'user', 'avatar', 'biography', 'phone', 'languages')
            read_only_fields = ('user',)
except Exception:

    UserProfileSerializer = None



class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):

    username_field = 'email'

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if not email or not password:
            raise AuthenticationFailed('Email and password are required.')


        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise AuthenticationFailed('No active account found with the given credentials.')
        except User.MultipleObjectsReturned:
            raise AuthenticationFailed('Multiple users with this email exist. Contact admin.')


        if not user.check_password(password):
            raise AuthenticationFailed('No active account found with the given credentials.')


        if not user.is_active:
            raise AuthenticationFailed('User account is disabled.')


        data = super().validate({
            'email': user.email, 'password': password
        })

        return data