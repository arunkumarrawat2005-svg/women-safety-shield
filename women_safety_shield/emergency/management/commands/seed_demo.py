from django.core.management.base import BaseCommand
from emergency.models import Emergency
from incident.models import IncidentEvent
from accounts.models import User
from django.utils import timezone
from datetime import timedelta
import random


class Command(BaseCommand):
    help = 'Seed demo emergency data'

    def handle(self, *args, **options):
        try:
            priya = User.objects.get(username='priya_sharma')
            ravi = User.objects.get(username='ravi_kumar')
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('Run initial setup first.'))
            return

        # Closed emergency
        if not Emergency.objects.filter(victim=priya, status='CLOSED').exists():
            e = Emergency.objects.create(
                victim=priya, latitude=19.0760, longitude=72.8777,
                status='CLOSED', trigger_type='button',
                assigned_guardian=ravi,
                created_at=timezone.now() - timedelta(hours=2),
                closed_at=timezone.now() - timedelta(hours=1),
                description='Felt followed near the market.'
            )
            events_data = [
                ('SOS_CREATED', -120), ('GUARDIAN_NOTIFIED', -118),
                ('GUARDIAN_ACCEPTED', -115), ('GUARDIAN_MOVING', -110),
                ('GUARDIAN_ARRIVED', -90), ('EMERGENCY_CLOSED', -60),
            ]
            for name, offset in events_data:
                IncidentEvent.objects.create(
                    emergency=e, event_name=name,
                    timestamp=timezone.now() + timedelta(minutes=offset),
                    latitude=19.0760 + random.uniform(-0.001, 0.001),
                    longitude=72.8777 + random.uniform(-0.001, 0.001),
                )
            self.stdout.write(self.style.SUCCESS(f'Created demo emergency #{e.id}'))

        self.stdout.write(self.style.SUCCESS('Demo data seeded!'))
