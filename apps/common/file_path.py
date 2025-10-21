import os
from django.utils import timezone
from django.utils.text import slugify

def avatar_upload_to(instance, filename):

    ext = filename.split('.')[-1]
    date = timezone.now().strftime('%Y%m%d')
    uname = slugify(getattr(getattr(instance, 'user', None), 'username', 'user'))
    filename = f'{uname}_{date}.{ext}'
    return os.path.join('avatars', filename)

def image_listing_upload_to(instance, filename):

    ext = filename.split('.')[-1]
    date = timezone.now().strftime('%Y%m%d%H%M%S')
    filename = f'{date}.{ext}'
    return os.path.join('listings', filename)