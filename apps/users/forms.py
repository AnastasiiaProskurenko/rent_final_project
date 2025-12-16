from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User
from apps.common.enums import UserRole

# Форма реєстрації
class RegisterForm(UserCreationForm):

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Email'})
    )

    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)

    role = forms.ChoiceField(
        choices=UserRole.choices,
        widget=forms.RadioSelect
    )

    phone = forms.CharField(required=False)

    class Meta:
        model = User
        fields = (
            'email',
            'username',
            'first_name',
            'last_name',
            'role',
            'phone',
            'password1',
            'password2',
        )

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Email already exists')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email'].lower()
        user.role = self.cleaned_data['role']

        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                phone=self.cleaned_data.get('phone')
            )
        return user

# Форма логіну по email
class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'placeholder': 'Enter your email',
            'autocomplete': 'email'
        })
    )
