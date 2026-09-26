import os
from django.core.management.base import BaseCommand
from django.db import connection
from accounts.models import User

class Command(BaseCommand):
    help = 'Purges all non-admin data across all database tables, leaving only the admin superuser'

    def handle(self, *args, **options):
        self.stdout.write("Starting database cleanup: removing all data except admin superuser...")

        # Clear legacy table if present
        try:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM guardians_guardian;")
        except Exception:
            pass

        # 1. Incident records
        try:
            from incident_records.models import IncidentRecordAuditLog, IdentityRevealRequest, IncidentBreadcrumb, IncidentRecord
            IncidentRecordAuditLog.objects.all().delete()
            IdentityRevealRequest.objects.all().delete()
            IncidentBreadcrumb.objects.all().delete()
            IncidentRecord.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("[OK] Cleared incident records."))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"[SKIP] incident_records: {e}"))

        # 2. Incidents
        try:
            from incident.models import IncidentReport, IncidentEvent
            IncidentEvent.objects.all().delete()
            IncidentReport.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("[OK] Cleared incidents."))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"[SKIP] incident: {e}"))

        # 3. Emergency & Tracking
        try:
            from emergency.models import Emergency
            from tracking.models import Location
            Location.objects.all().delete()
            Emergency.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("[OK] Cleared emergency SOS events and location tracks."))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"[SKIP] emergency/tracking: {e}"))

        # 4. Community & Escorts
        try:
            from local_residents.models import LocalResidentResponse, SafeEscortRequest, LocalResident
            LocalResidentResponse.objects.all().delete()
            SafeEscortRequest.objects.all().delete()
            LocalResident.objects.exclude(user__username='admin').delete()
            self.stdout.write(self.style.SUCCESS("[OK] Cleared local resident escorts and responses."))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"[SKIP] local_residents: {e}"))

        try:
            from community.models import TrustedContact, SafetyAlert
            SafetyAlert.objects.all().delete()
            TrustedContact.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("[OK] Cleared community alerts and trusted contacts."))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"[SKIP] community: {e}"))

        # 5. Organizations
        try:
            from organization.models import OrgResponse, OrgVolunteer, Organization
            OrgResponse.objects.all().delete()
            OrgVolunteer.objects.all().delete()
            Organization.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("[OK] Cleared organization responders."))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"[SKIP] organization: {e}"))

        # 6. Verification
        try:
            from verification.models import VerificationAuditLog, PolicePortalAccessLog, SafetyAssessment, VerificationRequest
            PolicePortalAccessLog.objects.all().delete()
            VerificationAuditLog.objects.all().delete()
            SafetyAssessment.objects.all().delete()
            VerificationRequest.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("[OK] Cleared verification requests and logs."))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"[SKIP] verification: {e}"))

        # 7. Notifications & Reports
        try:
            from notifications.models import Notification
            Notification.objects.all().delete()
        except Exception:
            pass

        try:
            from safety_map.models import SafetyReport
            SafetyReport.objects.all().delete()
        except Exception:
            pass

        # 8. Sessions & Admin log entries
        try:
            from django.contrib.sessions.models import Session
            from django.contrib.admin.models import LogEntry
            Session.objects.all().delete()
            LogEntry.objects.all().delete()
        except Exception:
            pass

        # 9. Delete non-admin users
        non_admin_users = User.objects.exclude(username='admin')
        count = non_admin_users.count()
        deleted_info = non_admin_users.delete()
        self.stdout.write(self.style.SUCCESS(f"[OK] Deleted {count} non-admin user accounts: {deleted_info}"))

        # 10. Ensure admin user exists and is configured
        admin_user = User.objects.filter(username='admin').first()
        if not admin_user:
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@womensafetyshield.com',
                password='AdminShield@2026',
                first_name='System',
                last_name='Administrator',
                role='admin',
                is_verified=True
            )
            self.stdout.write(self.style.SUCCESS("[OK] Re-created admin superuser."))
        else:
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.role = 'admin'
            admin_user.is_verified = True
            admin_user.set_password('AdminShield@2026')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("[OK] Admin account verified and password synced."))

        self.stdout.write(self.style.SUCCESS("[COMPLETE] Database reset completed successfully! Only 'admin' remains."))
