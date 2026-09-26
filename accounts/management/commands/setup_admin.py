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

        # Auto-seed verified community guardians / local residents if needed
        try:
            from local_residents.seed_data import seed_verified_residents
            from local_residents.models import LocalResident
            if LocalResident.objects.filter(is_verified=True).count() < 6:
                count = seed_verified_residents(admin_user=user)
                self.stdout.write(self.style.SUCCESS(f"[OK] Seeded {count} verified local community guardians and responders."))
            else:
                self.stdout.write(self.style.SUCCESS(f"[OK] Verified local guardians network is already active."))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"[WARNING] Could not seed local residents: {e}"))
