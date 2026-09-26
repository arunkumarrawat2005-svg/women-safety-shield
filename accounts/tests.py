from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


class UpgradeSpecTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create victim user
        self.victim = User.objects.create_user(
            username='victim_user',
            email='victim@test.com',
            password='password123',
            first_name='Ananya',
            last_name='Sharma',
            phone='9998887771',
            role='user'
        )

        # Create local resident user
        self.resident_user = User.objects.create_user(
            username='resident_user',
            email='resident@test.com',
            password='password123',
            first_name='Sunita',
            last_name='Devi',
            phone='9998887772',
            role='local_resident',
            is_verified=True
        )

        from local_residents.models import LocalResident
        self.resident = LocalResident.objects.create(
            user=self.resident_user,
            local_resident_type='volunteer',
            is_verified=True,
            is_available=True,
            latitude=19.0765,
            longitude=72.8775
        )

        # Create organization user & profile
        self.org_user = User.objects.create_user(
            username='org_admin',
            email='org@test.com',
            password='password123',
            first_name='Hospital',
            last_name='Security',
            role='organization',
            is_verified=True
        )
        from organization.models import Organization, OrgVolunteer
        self.org = Organization.objects.create(
            user=self.org_user,
            name='City Care Hospital',
            org_type='hospital',
            address='MG Road, Mumbai',
            contact_email='safety@citycare.org',
            contact_phone='9998887773',
            is_verified=True
        )

        self.org_volunteer_user = User.objects.create_user(
            username='org_guard',
            email='guard@citycare.org',
            password='password123',
            first_name='Rajesh',
            last_name='Kumar',
            phone='9998887774',
            role='user'
        )
        self.org_volunteer = OrgVolunteer.objects.create(
            organization=self.org,
            user=self.org_volunteer_user,
            approved_by_org=True,
            is_available=True,
            latitude=19.0770,
            longitude=72.8780
        )

    def test_01_user_role_and_consent(self):
        """Test local_resident role and location_data_consent flag."""
        self.assertEqual(self.resident_user.role, 'local_resident')
        self.assertTrue(self.resident_user.is_local_resident())
        self.assertTrue(self.resident_user.is_guardian())

        self.assertFalse(self.victim.location_data_consent)
        self.victim.location_data_consent = True
        self.victim.save()
        self.assertTrue(self.victim.location_data_consent)

    def test_02_three_channel_sos_dispatch(self):
        """Test SOS creation triggers Local Resident, Organization, and Gov Alerts in parallel."""
        from emergency.services import EmergencyService
        from local_residents.models import LocalResidentResponse
        from organization.models import OrgResponse
        from gov_alerts.models import GovAlert

        emergency = EmergencyService.create_emergency(
            user=self.victim,
            latitude=19.0760,
            longitude=72.8770,
            trigger_type='button',
            description='Test 3-channel emergency'
        )

        self.assertEqual(emergency.status, 'ACTIVE')

        # 1. Local Resident Network
        lr_resp = LocalResidentResponse.objects.filter(sos_event=emergency, resident=self.resident).first()
        self.assertIsNotNone(lr_resp)
        self.assertEqual(lr_resp.status, 'notified')

        # 2. Organization Network
        org_resp = OrgResponse.objects.filter(sos_event=emergency, organization=self.org).first()
        self.assertIsNotNone(org_resp)
        self.assertIsNotNone(org_resp.dashboard_alert_sent_at)

        # 3. Government channel
        gov_alert = GovAlert.objects.filter(sos_event=emergency).first()
        self.assertIsNotNone(gov_alert)
        self.assertEqual(gov_alert.delivery_status, 'DISPATCHED')

    def test_03_resident_acknowledgment_and_race_condition(self):
        """Test responder acknowledgment updates emergency and per-responder state."""
        from emergency.services import EmergencyService
        from local_residents.models import LocalResidentResponse

        emergency = EmergencyService.create_emergency(
            user=self.victim,
            latitude=19.0760,
            longitude=72.8770
        )

        EmergencyService.accept_emergency(emergency, self.resident_user)
        emergency.refresh_from_db()

        self.assertEqual(emergency.status, 'ACCEPTED')
        self.assertEqual(emergency.assigned_responder, self.resident_user)
        self.assertEqual(emergency.assigned_guardian, self.resident_user)

        lr_resp = LocalResidentResponse.objects.get(sos_event=emergency, resident=self.resident)
        self.assertEqual(lr_resp.status, 'acknowledged')
        self.assertIsNotNone(lr_resp.acknowledged_at)

    def test_04_verification_system(self):
        """Test verification request lifecycle and gating."""
        from verification.models import VerificationRequest
        v_req = VerificationRequest.objects.create(
            user=self.victim,
            aadhaar_document_ref='XXXX-XXXX-9999',
            status='pending'
        )
        self.assertEqual(v_req.status, 'pending')

        admin_user = User.objects.create_superuser('admin_tester', 'admin@test.com', 'pass123')
        self.client.force_authenticate(user=admin_user)
        resp = self.client.post(f'/api/verification/review/{v_req.id}/', {'status': 'approved', 'notes': 'Valid ID'})
        self.assertEqual(resp.status_code, 200)

        v_req.refresh_from_db()
        self.assertEqual(v_req.status, 'approved')
        self.assertTrue(v_req.user.is_verified)

    def test_05_safe_route_predictor(self):
        """Test AI safe route predictor candidate comparison."""
        self.client.force_authenticate(user=self.victim)
        resp = self.client.get('/api/safe-routes/compare/?from=19.0760,72.8770&to=19.0850,72.8850')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertGreaterEqual(len(data['candidate_routes']), 1)

        score_resp = self.client.get('/api/safe-routes/segment-score/?lat=19.0760&lng=72.8770')
        self.assertEqual(score_resp.status_code, 200)
        score_data = score_resp.json()
        self.assertTrue(score_data['success'])
        self.assertIn('predicted_safety_score', score_data)

    def test_06_anonymous_safety_report(self):
        """Test that is_anonymous=True conceals reporter user identity in API response."""
        from safety_map.models import SafetyReport
        report = SafetyReport.objects.create(
            user=self.victim,
            latitude=19.0760,
            longitude=72.8770,
            category='poor_lighting',
            is_anonymous=True
        )

        self.client.force_authenticate(user=self.victim)
        resp = self.client.get('/api/safety-map/')
        self.assertEqual(resp.status_code, 200)
        reports = resp.json().get('reports', [])
        target = next((r for r in reports if r['id'] == report.id), None)
        self.assertIsNotNone(target)
        self.assertIsNone(target['user'])
        self.assertEqual(target['user_name'], 'Anonymous')

    def test_07_backward_compatible_endpoints(self):
        """Test /api/guardians/nearby/ route returns residents seamlessly."""
        self.client.force_authenticate(user=self.victim)
        resp = self.client.get('/api/guardians/nearby/?lat=19.0760&lng=72.8770&radius=3')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('residents', data)
        self.assertIn('guardians', data)
        self.assertGreaterEqual(data['count'], 1)

    def test_08_user_access_levels_and_permissions(self):
        """Test access levels: Basic Users can seek help, but only verified helpers can assist."""
        from django.test import Client
        c = Client()

        # 1. Basic user properties
        basic_user = User.objects.create_user(
            username='basic_citizen',
            email='citizen@test.com',
            password='password123',
            first_name='Pooja',
            last_name='Verma',
            phone='9991112223',
            role='user'
        )
        self.assertTrue(basic_user.is_basic_user)
        self.assertTrue(basic_user.can_seek_help)
        self.assertFalse(basic_user.can_act_as_helper)
        self.assertFalse(basic_user.can_respond_to_sos)
        self.assertFalse(basic_user.can_join_guardian_network)
        self.assertEqual(basic_user.access_level_display, 'Basic User (Emergency Seeker Only)')

        # 2. Permission model page renders for anonymous & logged in
        resp = c.get('/permissions/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Anyone can seek help, but only verified users can provide community assistance.")

        # Logged in basic user views permission page
        c.login(username='basic_citizen', password='password123')
        resp = c.get('/permissions/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Basic User")
        self.assertContains(resp, "Upgrade to Verified Helper")

        # 3. Basic user cannot toggle availability in guardian network
        from django.urls import reverse
        from local_residents.models import LocalResident
        resident = LocalResident.objects.create(
            user=basic_user,
            local_resident_type='volunteer',
            is_verified=False,
            is_available=False
        )
        resp = c.post(reverse('toggle_availability'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/verification/status/', resp.url)
        resident.refresh_from_db()
        self.assertFalse(resident.is_available)

        # 4. Basic user cannot accept an SOS emergency
        from emergency.models import Emergency
        emerg = Emergency.objects.create(
            victim=self.victim,
            trigger_type='button',
            status='ACTIVE',
            latitude=19.0760,
            longitude=72.8770
        )
        resp = c.post(reverse('accept_emergency', args=[emerg.id]))
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/verification/status/', resp.url)
        emerg.refresh_from_db()
        self.assertEqual(emerg.status, 'ACTIVE')

        # 5. Verified helper CAN toggle availability and accept emergency
        verified_helper = User.objects.create_user(
            username='verified_helper',
            email='helper@test.com',
            password='password123',
            first_name='Kavita',
            last_name='Singh',
            phone='9993334445',
            role='local_resident',
            is_verified=True
        )
        v_resident = LocalResident.objects.create(
            user=verified_helper,
            local_resident_type='volunteer',
            is_verified=True,
            is_available=False,
            latitude=19.0762,
            longitude=72.8771
        )
        self.assertFalse(verified_helper.is_basic_user)
        self.assertTrue(verified_helper.can_seek_help)
        self.assertTrue(verified_helper.can_act_as_helper)
        self.assertTrue(verified_helper.can_respond_to_sos)
        self.assertTrue(verified_helper.can_join_guardian_network)
        self.assertEqual(verified_helper.access_level_display, 'Verified Community Guardian / Helper')
        c.login(username='verified_helper', password='password123')
        resp = c.post(reverse('toggle_availability'))
        self.assertEqual(resp.status_code, 302)
        v_resident.refresh_from_db()
        self.assertTrue(v_resident.is_available)

        resp = c.post(reverse('accept_emergency', args=[emerg.id]))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse('emergency_track', args=[emerg.id]), resp.url)
        emerg.refresh_from_db()
        self.assertEqual(emerg.status, 'ACCEPTED')

