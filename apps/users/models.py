from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import Avg

from apps.common.models import TimeModel
from apps.common.file_path import avatar_upload_to
from apps.common.validators import phone_validator
from apps.common.enums import UserRole


class User(AbstractUser, TimeModel):
    email = models.EmailField(unique=True)

    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.CUSTOMER
    )

    is_verified = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'.strip() or self.username

    # ✅ role-based helpers
    def is_customer(self):
        return self.role == UserRole.CUSTOMER

    def is_owner(self):
        return self.role == UserRole.OWNER

    def is_admin(self):
        return self.role == UserRole.ADMIN or self.is_superuser

    def __str__(self):
        return f'{self.get_full_name()} ({self.get_role_display()})'


class UserProfile(TimeModel):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='user'
    )

    phone = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        validators=[phone_validator]
    )
    avatar = models.ImageField(
        upload_to=avatar_upload_to,
        null=True,
        blank=True
    )
    biography = models.TextField(blank=True, null=True)
    languages = models.CharField(max_length=50, default='de')

    @property
    def listing_count(self):
        return getattr(
            self.user, 'listings', self.user.listings.none()
        ).filter(is_active=True, is_deleted=False).count()

    @property
    def rating(self):
        from apps.reviews.models import OwnerRating
        avg = OwnerRating.objects.filter(
            owner=self.user
        ).aggregate(avg=Avg('rating'))['avg']
        return round(avg or 0.0, 2)

    def __str__(self):
        return f'Profile: {self.user.get_full_name()} ({self.user.get_role_display()})'


class RefreshTokenRecord(TimeModel):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='refresh_tokens'
    )
    jti = models.CharField(max_length=255, unique=True)
    token = models.TextField(null=True, blank=True)
    revoked = models.BooleanField(default=False)
    expires_at = models.DateTimeField(null=True, blank=True)

    def revoke(self):
        self.revoked = True
        self.save(update_fields=['revoked'])
