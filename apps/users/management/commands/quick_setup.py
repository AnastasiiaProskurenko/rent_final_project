from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Quick setup: create superuser and generate test data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before setup'
        )

    def handle(self, *args, **options):
        self.stdout.write('Starting quick setup...')
        

        self.stdout.write('Creating superuser...')
        call_command('create_superuser')
        

        self.stdout.write('Generating test data...')
        clear_flag = ['--clear'] if options['clear'] else []
        call_command('generate_fake_data', 
                    '--users', '20', 
                    '--listings', '30', 
                    '--bookings', '50', 
                    '--reviews', '25',
                    '--notifications', '40',
                    '--payments', '30',
                    '--search-queries', '60',
                    '--listing-views', '100',
                    *clear_flag)
        

        self.stdout.write('Saving user credentials...')
        call_command('save_passwords', '--format', 'json')
        
        self.stdout.write(
            self.style.SUCCESS('Quick setup completed!')
        )
        self.stdout.write('')
        self.stdout.write('Login credentials:')
        self.stdout.write('Superuser: admin / admin123')
        self.stdout.write('All test users: 1111')
        self.stdout.write('  - owner_1, owner_2, ... (30% of users)')
        self.stdout.write('  - customer_1, customer_2, ... (70% of users)')
        self.stdout.write('')
        self.stdout.write('API endpoints:')
        self.stdout.write('- Admin: http://localhost:8000/admin/')
        self.stdout.write('- API docs: http://localhost:8000/api/schema/swagger-ui/')
        self.stdout.write('- Token: http://localhost:8000/api/auth/token/')
        self.stdout.write('')
        self.stdout.write('Files created:')
        self.stdout.write('- user_credentials.json (user login info)')
