from django.apps import apps
from django.db.models.signals import post_save
from django.dispatch import receiver

Listing = apps.get_model('listings', 'Listing')
Notification = apps.get_model('notifications', 'Notification')


@receiver(post_save, sender=Listing)
def create_listing_notification(sender, instance, created, **kwargs):
    if not created:
        return

    Notification.objects.create(
        user=instance.owner,
        title='Нове оголошення створене',
        message=f'Оголошення {instance.title} створене',
        notification_type='LISTING',
        related_object_id=instance.id,
        related_object_type='listing',
    )
