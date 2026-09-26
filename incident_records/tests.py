from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError, PermissionDenied

from emergency.models import Emergency
from emergency.services import EmergencyService
from local_residents.models import LocalResident
from organization.models import Organization, OrgVolunteer
from gov_alerts.models import GovAlert
from incident_records.models import IncidentRecord, IncidentBreadcrumb
from incident_records.services import IncidentRecordService

User = get_user_model()


class ResponderProtectionIncidentRecordTests(TestCase):

    def setUp(self):
        # 1. Victim User
        self.victim = User.objects.create_user(
            username='victim_user',
            email='victim@test.com',
            password='Password123!',
            role='user',
            first_name='Ananya',
            last_name='Sharma',
            phone='+919876543210'
        )

        # 2. Local Resident Responder User
        self.resident_user = User.objects.create_user(
            username='resident_responder',
            email='resident@test.com',
            password='Password123!',
            role='local_resident',
            first_name='Vikram',
            last_name='Singh',
            phone='+919811122233',
            is_verified=True
        )
        self.resident_profile = LocalResident.objects.create(
            user=self.resident_user,
            local_resident_type='citizen',
            is_verified=True,
            is_available=True,
            trust_score=9.2,
            latitude=28.4744,
            longitude=77.5039
        )

        # 3. Org Volunteer Responder User
        self.org_user = User.objects.create_user(
            username='org_admin',
            email='org@test.com',
            password='Password123!',
            role='organization',
            first_name='NGO',
            last_name='Director'
        )
        self.org = Organization.objects.create(
            user=self.org_user,
            name='Women Safety Relief Force',
            org_type='ngo',
            address='Sector 62, Noida',
            contact_email='contact@wsrf.org',
            contact_phone='+919999988888',
            is_verified=True
        )
        self.volunteer_user = User.objects.create_user(
            username='org_volunteer',
            email='volunteer@test.com',
            password='Password123!',
            role='organization',
            first_name='Pooja',
            last_name='Verma',
            phone='+919844455566'
        )
        self.org_volunteer = OrgVolunteer.objects.create(
            organization=self.org,
            user=self.volunteer_user,
            verification_status='verified',
            approved_by_org=True,
            is_available=True
        )

        # 4. Staff Admin User
        self.admin_user = User.objects.create_superuser(
            username='admin_officer',
            email='admin@wss.gov',
            password='Password123!',
            first_name='Super',
            last_name='Admin'
        )

        # Staff user without permission
        self.regular_staff = User.objects.create_user(
            username='regular_staff',
            email='staff@wss.gov',
            password='Password123!',
            is_staff=True,
            first_name='Staff',
            last_name='Member'
        )

        # Create active emergency
        self.emergency = Emergency.objects.create(
            victim=self.victim,
            latitude=28.47440,
            longitude=77.50390,
            address="Knowledge Park III, Greater Noida",
            status='ACTIVE'
        )

    def test_feature1_dispatch_record_creation_and_immutability(self):
        """Feature 1: Test server-side tamper-proof dispatch record creation."""
        # Responder accepts emergency
        EmergencyService.accept_emergency(self.emergency, self.resident_user)

        record = IncidentRecord.objects.filter(sos=self.emergency, responder=self.resident_user).first()
        self.assertIsNotNone(record)
        self.assertEqual(record.network_source, 'local_resident')
        self.assertEqual(record.status, 'dispatched')
        self.assertIsNotNone(record.acknowledged_at)
        self.assertTrue(record.masked_responder_id.startswith("Verified Responder #LR-"))

        # Test immutability: modifying acknowledged_at must fail clean()
        orig_time = record.acknowledged_at
        record.acknowledged_at = timezone.now() + timezone.timedelta(hours=2)
        with self.assertRaises(ValidationError):
            record.clean()

        # Test breadcrumb immutability
        breadcrumb = IncidentBreadcrumb.objects.create(
            incident_record=record,
            latitude=28.4800,
            longitude=77.5100,
            timestamp=timezone.now()
        )
        self.assertIsNotNone(breadcrumb.id)
        # Attempting to update breadcrumb must raise ValidationError
        breadcrumb.latitude = 28.4900
        with self.assertRaises(ValidationError):
            breadcrumb.save()

        # Attempting to delete breadcrumb must raise ValidationError
        with self.assertRaises(ValidationError):
            breadcrumb.delete()

    def test_feature1_and_3_breadcrumb_and_inferred_arrival(self):
        """Feature 1 & 3: Test breadcrumb trail logging and automatic arrival inference at <= 50m."""
        EmergencyService.accept_emergency(self.emergency, self.resident_user)
        record = IncidentRecord.objects.get(sos=self.emergency, responder=self.resident_user)

        # 1. Coordinate far away (> 500 meters)
        res1 = IncidentRecordService.record_location_breadcrumb(
            responder_user=self.resident_user,
            latitude=self.emergency.latitude + 0.006,  # ~660 meters away
            longitude=self.emergency.longitude + 0.006,
            emergency_id=self.emergency.id
        )
        self.assertIsNotNone(res1)
        self.assertFalse(res1['arrived'])
        self.assertFalse(res1['arrival_triggered'])
        record.refresh_from_db()
        self.assertIsNone(record.arrival_at)
        self.assertEqual(record.status, 'en_route')

        # 2. Coordinate within 30 meters of victim (arrival trigger)
        res2 = IncidentRecordService.record_location_breadcrumb(
            responder_user=self.resident_user,
            latitude=self.emergency.latitude + 0.0001,  # ~11 meters away
            longitude=self.emergency.longitude + 0.0001,
            emergency_id=self.emergency.id
        )
        self.assertTrue(res2['arrived'])
        self.assertTrue(res2['arrival_triggered'])
        record.refresh_from_db()
        self.assertIsNotNone(record.arrival_at)
        self.assertTrue(record.is_arrival_detected)
        self.assertEqual(record.status, 'arrived')

        # Once arrival_at is set, attempting to wipe or change it must raise ValidationError
        record.arrival_at = None
        with self.assertRaises(ValidationError):
            record.clean()

    def test_feature2_automatic_police_handoff(self):
        """Feature 2: Test automatic police handoff packet generation."""
        EmergencyService.accept_emergency(self.emergency, self.volunteer_user)
        record = IncidentRecord.objects.get(sos=self.emergency, responder=self.volunteer_user)

        self.assertEqual(record.network_source, 'organization')
        self.assertIsNotNone(record.police_notified_at)
        payload = record.police_notification_payload
        self.assertEqual(payload['emergency_id'], self.emergency.id)
        self.assertEqual(payload['dispatched_responder']['full_name'], 'Pooja Verma')
        self.assertEqual(payload['dispatched_responder']['organization_name'], 'Women Safety Relief Force')

        # Verify GovAlert model was populated
        gov_alert = GovAlert.objects.filter(sos_event=self.emergency).latest('sent_at')
        self.assertIn('OFFICIAL PLATFORM DISPATCH', gov_alert.response_payload.get('certificate_notice', ''))

    def test_feature4_identity_masking_and_mutual_reveal(self):
        """Feature 4: Test victim sees masked identity and mutual opt-in reveal workflow."""
        EmergencyService.accept_emergency(self.emergency, self.resident_user)
        record = IncidentRecord.objects.get(sos=self.emergency, responder=self.resident_user)

        # Victim inspects responder info
        victim_info = IncidentRecordService.get_masked_responder_info(self.emergency, self.victim)
        self.assertTrue(victim_info['is_masked'])
        self.assertIn('Verified Responder #LR-', victim_info['name'])
        self.assertNotIn('Vikram Singh', victim_info['name'])
        self.assertIn('+91 1800-', victim_info['phone'])

        # Victim initiates identity reveal request
        req = IncidentRecordService.request_identity_reveal(self.victim, self.emergency.id, notes="Thank you for helping")
        self.assertEqual(req.status, 'pending')

        # Victim info still masked while pending
        victim_info_pending = IncidentRecordService.get_masked_responder_info(self.emergency, self.victim)
        self.assertTrue(victim_info_pending['is_masked'])

        # Responder declines -> remains masked
        IncidentRecordService.respond_to_reveal_request(self.resident_user, req.id, consent=False)
        req.refresh_from_db()
        self.assertEqual(req.status, 'declined')
        victim_info_declined = IncidentRecordService.get_masked_responder_info(self.emergency, self.victim)
        self.assertTrue(victim_info_declined['is_masked'])

        # Responder consents -> unmasked
        IncidentRecordService.respond_to_reveal_request(self.resident_user, req.id, consent=True)
        victim_info_consented = IncidentRecordService.get_masked_responder_info(self.emergency, self.victim)
        self.assertFalse(victim_info_consented['is_masked'])
        self.assertEqual(victim_info_consented['name'], 'Vikram Singh')
        self.assertEqual(victim_info_consented['phone'], '+919811122233')

    def test_feature5_admin_access_controls_and_audit(self):
        """Feature 5: Test scoped admin permissions and mandatory audit logging."""
        EmergencyService.accept_emergency(self.emergency, self.resident_user)
        record = IncidentRecord.objects.get(sos=self.emergency, responder=self.resident_user)

        # Regular staff without permission cannot unmask
        with self.assertRaises(PermissionDenied):
            IncidentRecordService.log_admin_identity_access(
                admin_user=self.regular_staff,
                incident_record=record,
                reason="Routine check"
            )

        # Missing or empty reason rejected
        with self.assertRaises(ValueError):
            IncidentRecordService.log_admin_identity_access(
                admin_user=self.admin_user,
                incident_record=record,
                reason=""
            )

        # Superuser / authorized admin with valid reason succeeds and writes to IncidentRecordAuditLog
        audit = IncidentRecordService.log_admin_identity_access(
            admin_user=self.admin_user,
            incident_record=record,
            reason="Official Inquiry FIR #2026/891 Case Verification",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 Inspector"
        )
        self.assertIsNotNone(audit.id)
        self.assertEqual(audit.admin_user, self.admin_user)
        self.assertEqual(audit.incident_record, record)
        self.assertEqual(audit.ip_address, "192.168.1.100")
        self.assertIn("FIR #2026/891", audit.access_reason)

        # Confirm audit log count
        self.assertEqual(record.audit_logs.count(), 1)
