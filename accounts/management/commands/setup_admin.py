import os
from django.core.management.base import BaseCommand
from accounts.models import User

class Command(BaseCommand):
    help = 'Automatically provisions admin superuser account on production deployment'

    def handle(self, *args, **options):
        username = os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin')
        email = os.getenv('DJANGO_SUPERUSER_EMAIL', 'admin@womensafetyshield.com')
        password = os.getenv('DJANGO_SUPERUSER_PASSWORD', 'AdminShield@2026')

        user = User.objects.filter(username=username).first()
        if not user:
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                first_name='System',
                last_name='Administrator',
                role='admin',
                is_verified=True
            )
            self.stdout.write(self.style.SUCCESS(f"[OK] Admin account '{username}' created successfully!"))
        else:
            user.is_staff = True
            user.is_superuser = True
            user.role = 'admin'
            user.is_verified = True
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"[OK] Existing admin account '{username}' updated and password synced."))
