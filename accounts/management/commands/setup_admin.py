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

        # Ensure all existing real verified users have an active LocalResident profile
        try:
            from local_residents.models import LocalResident
            verified_users = User.objects.filter(is_verified=True).exclude(role='admin')
            synced_count = 0
            for vu in verified_users:
                res, created = LocalResident.objects.get_or_create(
                    user=vu,
                    defaults={
                        'local_resident_type': 'citizen' if vu.role == 'user' else (vu.role if vu.role in ['volunteer', 'security', 'ngo', 'citizen'] else 'citizen'),
                        'city': vu.city or 'Delhi NCR',
                        'area': vu.address or vu.city or 'Central Zone',
                        'badge_title': 'Verified Citizen Guardian',
                    }
                )
                res.is_verified = True
                res.is_available = True
                res.save()
                synced_count += 1
            self.stdout.write(self.style.SUCCESS(f"[OK] Synced {synced_count} real verified citizen profiles in database."))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"[WARNING] Could not sync verified users: {e}"))
