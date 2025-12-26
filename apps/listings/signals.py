import logging
from django.apps import apps
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.apps import apps

logger = logging.getLogger(__name__)

Listing = apps.get_model('listings', 'Listing')
Notification = apps.get_model('notifications', 'Notification')


@receiver(post_save, sender=Listing)
def create_listing_notification(sender, instance, created, **kwargs):
    if not created:
        return

    title = 'Нове оголошення створене'

    notif=Notification.objects.create(
        user=instance.owner,
        title=title,
        message=f'Оголошення {instance.title} створене',
        notification_type='LISTING',
        related_object_id=instance.id,
        related_object_type='listing',
    )
    logger.info(
        "Notification created. notification_id=%s user_id=%s title=%s",
        notif.id,
        instance.id,
        title,
    )
