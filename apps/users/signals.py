import logging

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth.models import Group
from django.apps import apps

User = apps.get_model('users', 'User')
Notification = apps.get_model('notifications', 'Notification')

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def add_default_group(sender, instance, created, **kwargs):
    if not created:
        return

    try:
        customers_group = Group.objects.get(name='Customers')
        instance.groups.add(customers_group)
    except Group.DoesNotExist:

        pass


@receiver(post_save, sender=User)
def create_user_creation_notification(sender, instance, created, **kwargs):
    if not created:
        return

    title = f'User {instance.first_name} {instance.last_name} створений'

    Notification.objects.create(
        user=instance,
        title=title,
        message=title,
        notification_type='SYSTEM',
    )
    logger.info(title)
    print(title)
