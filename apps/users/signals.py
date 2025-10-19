from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth.models import Group
from django.apps import apps

User = apps.get_model('users', 'User')

@receiver(post_save, sender=User)
def add_default_group(sender, instance, created, **kwargs):
    if not created:
        return

    try:
        customers_group = Group.objects.get(name='Customers')
        instance.groups.add(customers_group)
    except Group.DoesNotExist:

        pass