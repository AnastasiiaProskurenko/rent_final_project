import logging

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from django.apps import apps

logger = logging.getLogger(__name__)

User = apps.get_model("users", "User")
Notification = apps.get_model("notifications", "Notification")


@receiver(post_save, sender=User)
def add_default_group(sender, instance, created, **kwargs):
    """
    Додає нового користувача в групу Customers.
    Якщо групи немає — створює її (без пустих pass).
    """
    if not created:
        return

    group_name = "Customers"
    group, was_created = Group.objects.get_or_create(name=group_name)
    instance.groups.add(group)

    if was_created:
        logger.info("Group '%s' created automatically. user_id=%s", group_name, instance.id)

    logger.info(
        "User added to group '%s'. user_id=%s email=%s",
        group_name,
        instance.id,
        getattr(instance, "email", None),
    )


@receiver(post_save, sender=User)
def create_user_creation_notification(sender, instance, created, **kwargs):
    """
    Створює системне повідомлення про створення користувача.
    """
    if not created:
        return

    full_name = f"{(instance.first_name or '').strip()} {(instance.last_name or '').strip()}".strip()
    display_name = full_name or getattr(instance, "email", "") or f"id={instance.id}"

    title = f"User {display_name} створений"

    notif = Notification.objects.create(
        user=instance,
        title=title,
        message=title,
        notification_type="SYSTEM",
    )

    logger.info(
        "Notification created. notification_id=%s user_id=%s title=%s",
        notif.id,
        instance.id,
        title,
    )
