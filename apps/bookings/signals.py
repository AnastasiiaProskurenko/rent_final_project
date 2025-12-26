from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from apps.bookings.models import Booking
from apps.common.enums import BookingStatus
from apps.notifications.models import Notification


STATUS_MESSAGES = {
    BookingStatus.PENDING: 'очікує підтвердження',
    BookingStatus.CONFIRMED: 'підтверджено',
    BookingStatus.CANCELLED: 'скасовано',
    BookingStatus.COMPLETED: 'завершено',
    BookingStatus.REJECTED: 'відхилено',
    BookingStatus.IN_PROGRESS: 'у процесі',
    BookingStatus.EXPIRED: 'прострочено',
}


@receiver(pre_save, sender=Booking)
def store_previous_status(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        instance._previous_status = Booking.objects.get(pk=instance.pk).status
    except Booking.DoesNotExist:
        instance._previous_status = None


@receiver(post_save, sender=Booking)
def create_booking_notifications(sender, instance, created, update_fields=None, **kwargs):
    if created:
        Notification.objects.create(
            user=instance.customer,
            title='Нове бронювання',
            message=f'Бронювання #{instance.pk} створено, чекайте підтвердження',
            notification_type='BOOKING',
            related_object_id=instance.pk,
            related_object_type='booking',
        )
        Notification.objects.create(
            user=instance.listing.owner,
            title='Новий запит на бронювання',
            message=f'Новий букінг #{instance.pk}, прийміть або скасуйте',
            notification_type='BOOKING',
            related_object_id=instance.pk,
            related_object_type='booking',
        )
        return

    previous_status = getattr(instance, '_previous_status', None)
    status_changed = (
        (update_fields and 'status' in update_fields)
        or (previous_status and previous_status != instance.status)
    )

    if not status_changed:
        return

    status_message = STATUS_MESSAGES.get(
        instance.status,
        instance.get_status_display().lower(),
    )

    Notification.objects.create(
        user=instance.customer,
        title='Статус бронювання оновлено',
        message=f'Бронювання #{instance.pk} {status_message}.',
        notification_type='BOOKING',
        related_object_id=instance.pk,
        related_object_type='booking',
    )
