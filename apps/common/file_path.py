import os
from django.utils import timezone
from django.utils.text import slugify

def avatar_upload_to(instance, filename):

    ext = filename.split('.')[-1]
    date = timezone.now().strftime('%Y%m%d')
    uid = getattr(getattr(instance, 'user', None), 'id', 'anon')
    uname = slugify(getattr(getattr(instance, 'user', None), 'username', 'user'))
    filename = f'{uid}_{uname}_{date}.{ext}'
    return os.path.join('avatars', filename)

def image_listing_upload_to(instance, filename):

    ext = filename.split('.')[-1]
    date = timezone.now().strftime('%Y%m%d%H%M%S')
    lid = getattr(instance, 'id', 'listing')
    title = slugify(getattr(instance, 'title', 'listing'))[:40]
    filename = f'{lid}_{title}_{date}.{ext}'
    return os.path.join('listings', filename)