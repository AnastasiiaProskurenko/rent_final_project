from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0002_create_groups'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='role',
        ),
    ]