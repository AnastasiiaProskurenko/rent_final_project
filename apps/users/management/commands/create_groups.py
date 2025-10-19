from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.apps import apps
from django.contrib.contenttypes.models import ContentType

class Command(BaseCommand):
    help = 'Create default groups and assign model permissions'

    def handle(self, *args, **options):

        groups_config = {
            'Owners': {
                'listings.Listing': ['add', 'change', 'delete', 'view'],
                'listings.ListingPhoto': ['add', 'change', 'delete', 'view'],
                'bookings.Booking': ['view'],
            },
            'Customers': {
                'bookings.Booking': ['add', 'change', 'view', 'delete'],
                'listings.Listing': ['view'],
                'reviews.Review': ['add', 'change', 'view'],
            },
            'Managers': {

                'listings.Listing': ['change', 'view'],
                'bookings.Booking': ['change', 'view'],
                'reviews.Review': ['change', 'view'],
            },
            'Admins': {

                'listings.Listing': ['add', 'change', 'delete', 'view'],
                'bookings.Booking': ['add', 'change', 'delete', 'view'],
                'reviews.Review': ['add', 'change', 'delete', 'view'],
                'users.User': ['add', 'change', 'delete', 'view'],
            },
        }

        for group_name, models_perms in groups_config.items():
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Group created: {group_name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Group exists: {group_name}'))

            for model_label, actions in models_perms.items():
                app_label, model_name = model_label.split('.')
                try:
                    model = apps.get_model(app_label, model_name)
                except LookupError:
                    self.stdout.write(self.style.ERROR(f'Model not found: {model_label}'))
                    continue
                ct = ContentType.objects.get_for_model(model)
                for action in actions:
                    codename = f'{action}_{model._meta.model_name}'
                    try:
                        perm = Permission.objects.get(content_type=ct, codename=codename)
                        group.permissions.add(perm)
                        self.stdout.write(self.style.SUCCESS(f'Added perm {codename} to group {group_name}'))
                    except Permission.DoesNotExist:
                        self.stdout.write(self.style.ERROR(f'Permission not found: {codename}'))

        self.stdout.write(self.style.SUCCESS('Groups and permissions setup finished.'))