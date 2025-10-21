from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Створює групи користувачів (Customers, Owners, Admins) з правами'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Початок створення груп...'))

        # Видалити старі групи
        Group.objects.filter(name__in=['Customers', 'Owners', 'Admins']).delete()
        self.stdout.write('🗑️  Старі групи видалено')

        try:
            from apps.listings.models import Listing
            from apps.bookings.models import Booking
            from apps.payments.models import Payment
            from apps.reviews.models import Review

            listing_ct = ContentType.objects.get_for_model(Listing)
            booking_ct = ContentType.objects.get_for_model(Booking)
            payment_ct = ContentType.objects.get_for_model(Payment)
            review_ct = ContentType.objects.get_for_model(Review)

            self.stdout.write(self.style.SUCCESS('✅ ContentTypes отримані'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Помилка: {e}'))
            return

        # ============================================
        # CUSTOMERS
        # ============================================
        customers = Group.objects.create(name='Customers')
        customer_permissions = []

        try:
            customer_permissions.extend([
                Permission.objects.get(codename='view_listing', content_type=listing_ct),
                Permission.objects.get(codename='add_booking', content_type=booking_ct),
                Permission.objects.get(codename='view_booking', content_type=booking_ct),
                Permission.objects.get(codename='change_booking', content_type=booking_ct),
                Permission.objects.get(codename='add_payment', content_type=payment_ct),
                Permission.objects.get(codename='view_payment', content_type=payment_ct),
                Permission.objects.get(codename='add_review', content_type=review_ct),
                Permission.objects.get(codename='view_review', content_type=review_ct),
            ])
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'⚠️  Деякі permissions не знайдено: {e}'))

        customers.permissions.set(customer_permissions)
        self.stdout.write(self.style.SUCCESS(f'✅ Customers: {len(customer_permissions)} прав'))

        # ============================================
        # OWNERS
        # ============================================
        owners = Group.objects.create(name='Owners')
        owner_permissions = customer_permissions.copy()

        try:
            owner_permissions.extend([
                Permission.objects.get(codename='add_listing', content_type=listing_ct),
                Permission.objects.get(codename='change_listing', content_type=listing_ct),
                Permission.objects.get(codename='delete_listing', content_type=listing_ct),
            ])
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'⚠️  Деякі permissions не знайдено: {e}'))

        owners.permissions.set(owner_permissions)
        self.stdout.write(self.style.SUCCESS(f'✅ Owners: {len(owner_permissions)} прав'))

        # ============================================
        # ADMINS
        # ============================================
        admins = Group.objects.create(name='Admins')
        admin_permissions = Permission.objects.filter(
            content_type__in=[listing_ct, booking_ct, payment_ct, review_ct]
        )
        admins.permissions.set(admin_permissions)
        self.stdout.write(self.style.SUCCESS(f'✅ Admins: {admin_permissions.count()} прав'))

        # ============================================
        # ПІДСУМОК
        # ============================================
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 50))
        self.stdout.write(self.style.SUCCESS('🎉 ВСІ ГРУПИ СТВОРЕНІ!'))
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(f'Customers: {customers.permissions.count()} прав')
        self.stdout.write(f'Owners: {owners.permissions.count()} прав')
        self.stdout.write(f'Admins: {admins.permissions.count()} прав')
        self.stdout.write(self.style.SUCCESS('=' * 50))