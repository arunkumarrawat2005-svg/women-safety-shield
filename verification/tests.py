from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from verification.models import VerificationRequest, SafetyAssessment, VerificationAuditLog, PolicePortalAccessLog
from verification.services import SafetyAssessmentService


class UserOnboardingAndVerificationTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Normal Citizen
        self.citizen = User.objects.create_user(
            username='priya_citizen',
            email='priya@example.com',
            password='testpassword123',
            first_name='Priya',
            last_name='Sharma',
            phone='9876543210',
            role='user'
        )
        # Police Officer
        self.officer = User.objects.create_user(
            username='inspector_rajesh',
            email='rajesh.police@gov.in',
            password='testpassword123',
            first_name='Rajesh',
            last_name='Kumar',
            phone='9811223344',
            role='police'
        )
        # Admin Staff
        self.admin_user = User.objects.create_user(
            username='admin_shield',
            email='admin@womensafetyshield.org',
            password='testpassword123',
            first_name='Admin',
            last_name='Officer',
            role='admin',
            is_staff=True
        )

    def test_how_it_works_page(self):
        """Test How It Works page renders 4 pillars and trust architecture."""
        response = self.client.get(reverse('how_it_works'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Understand")
        self.assertContains(response, "Verify")
        self.assertContains(response, "Protect")
        self.assertContains(response, "Stay Protected")
        self.assertContains(response, "One Tap SOS")
        self.assertContains(response, "Live Radius Map")
        self.assertContains(response, "Verified Trust")
        self.assertContains(response, "Identity Verified")


    def test_registration_and_redirect_to_verification(self):
        """Test new user registration seamlessly directs to Step 2: Verification."""
        post_data = {
            'username': 'anita_verma',
            'first_name': 'Anita',
            'last_name': 'Verma',
            'email': 'anita@example.com',
            'phone': '9822334455',
            'date_of_birth': '1998-05-12',
            'city': 'South Delhi',
            'role': 'user',
            'password1': 'ShieldPass@2026',
            'password2': 'ShieldPass@2026',
        }
        response = self.client.post(reverse('register'), post_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('verification_status'))
        created_user = User.objects.get(username='anita_verma')
        self.assertFalse(created_user.is_verified)
        self.assertFalse(created_user.badge_identity_verified)

    def test_submit_identity_and_safety_assessment(self):
        """Test Step 2 & 3: Citizen submits ID document and completes 6 Likert questions."""
        self.client.login(username='priya_citizen', password='testpassword123')
        post_data = {
            'document_type': 'aadhaar',
            'document_number': '123456789012',
            'name': 'Priya Sharma',
            'dob': '1996-08-20',
            'consent_data_processing': 'on',
            # 6 Likert questions (1 to 5)
            'q1': '5',  # Strongly Agree
            'q2': '5',  # Strongly Agree
            'q3': '5',  # Strongly Agree
            'q4': '5',  # Strongly Agree
            'q5': '4',  # Agree
            'q6': '4',  # Agree
        }
        response = self.client.post(reverse('verification_status'), post_data)
        self.assertEqual(response.status_code, 302)

        # Check VerificationRequest created
        req = VerificationRequest.objects.get(user=self.citizen)
        self.assertEqual(req.status, 'pending')
        self.assertEqual(req.document_type, 'aadhaar')
        self.assertEqual(req.masked_document_number, 'XXXXXXXX9012')
        self.assertTrue(req.consent_data_processing)

        # Check SafetyAssessment created & scores computed
        assessment = SafetyAssessment.objects.get(user=self.citizen)
        self.assertEqual(assessment.q1_responsibility, 5)
        self.assertEqual(assessment.q2_willingness, 5)
        self.assertEqual(assessment.community_help_score, 100.0)
        self.assertEqual(assessment.womens_safety_score, 100.0)
        self.assertIn("Advisory Signal Notice", assessment.ai_disclaimer)
        self.assertIn("Orientation Overview", assessment.ai_summary)

        # Check VerificationAuditLog
        audit_log = VerificationAuditLog.objects.filter(verification_request=req).first()
        self.assertIsNotNone(audit_log)
        self.assertEqual(audit_log.new_status, 'pending')

    def test_admin_verification_dashboard_and_actions(self):
        """Test Admin can inspect applications, approve, reject, or request re-verification."""
        # Create a pending request
        req = VerificationRequest.objects.create(
            user=self.citizen,
            document_type='aadhaar',
            document_number='987654321234',
            status='pending'
        )

        # Non-admin forbidden
        self.client.login(username='priya_citizen', password='testpassword123')
        resp = self.client.get(reverse('admin_verification_dashboard'))
        self.assertEqual(resp.status_code, 302)

        # Admin authorized
        self.client.login(username='admin_shield', password='testpassword123')
        resp = self.client.get(reverse('admin_verification_dashboard'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Citizen &amp; Responder Verification Control")
        self.assertContains(resp, "priya_citizen")

        # Admin approves
        action_resp = self.client.post(
            reverse('admin_verification_action', args=[req.id]),
            {'action': 'approve', 'reason': 'All documents checked and verified.'}
        )
        self.assertEqual(action_resp.status_code, 302)
        req.refresh_from_db()
        self.assertEqual(req.status, 'approved')
        self.citizen.refresh_from_db()
        self.assertTrue(self.citizen.is_verified)
        self.assertTrue(self.citizen.badge_identity_verified)

    def test_police_portal_rbac_and_audit_logging(self):
        """Test Police Portal enforces RBAC, data minimization, and audit logs."""
        # Citizen blocked
        self.client.login(username='priya_citizen', password='testpassword123')
        resp = self.client.get(reverse('police_portal'))
        self.assertEqual(resp.status_code, 302)

        # Police Officer authorized
        self.client.login(username='inspector_rajesh', password='testpassword123')
        resp = self.client.get(reverse('police_portal'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Government &amp; Police Verification Portal")
        self.assertContains(resp, "RBAC &amp; Data Minimization Active")

        # Execute search with logged purpose
        search_resp = self.client.get(reverse('police_portal'), {
            'q': 'priya',
            'purpose': 'Investigating Emergency Call #112-9843'
        })
        self.assertEqual(search_resp.status_code, 200)
        self.assertContains(search_resp, "Priya Sharma")

        # Verify access audit log created
        log = PolicePortalAccessLog.objects.filter(officer=self.officer).first()
        self.assertIsNotNone(log)
        self.assertIn("112-9843", log.access_purpose)
        self.assertIn("priya", log.search_query)

    def test_trust_badges_architecture(self):
        """Test trust badges reflect actual verified attributes."""
        user = self.citizen
        # Initially not identity verified
        self.assertFalse(user.badge_identity_verified)
        self.assertFalse(user.badge_community_verified)
        # Has phone and email -> secure account
        self.assertTrue(user.badge_secure_account)

        # After approval
        user.is_verified = True
        user.save()
        self.assertTrue(user.badge_identity_verified)
