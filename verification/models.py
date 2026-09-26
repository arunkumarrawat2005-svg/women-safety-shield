from django.db import models
from django.conf import settings


class VerificationRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('under_review', 'Under Review'),
        ('approved', 'Verified'),
        ('rejected', 'Rejected'),
        ('reverification_required', 'Re-verification Required'),
    ]

    DOCUMENT_TYPES = [
        ('aadhaar', 'Aadhaar Card'),
        ('pan', 'PAN Card'),
        ('voter_id', 'Voter ID Card'),
        ('passport', 'Passport'),
        ('driving_license', 'Driving License'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='verification_requests')
    
    # Document Selection & Data
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPES, default='aadhaar')
    document_number = models.CharField(max_length=100, blank=True)
    document_file = models.FileField(upload_to='verification_docs/id_docs/', null=True, blank=True)
    
    # Legacy / specific multi-upload references
    aadhaar_document_ref = models.CharField(max_length=255, blank=True, help_text="Secure verification token / masked identifier")
    additional_documents = models.FileField(upload_to='verification_docs/', null=True, blank=True)
    aadhaar_image = models.FileField(upload_to='verification_docs/aadhaar/', null=True, blank=True)
    pan_image = models.FileField(upload_to='verification_docs/pan/', null=True, blank=True)
    selfie_image = models.FileField(upload_to='verification_docs/selfies/', null=True, blank=True)

    # OCR Extracted Fields
    ocr_name = models.CharField(max_length=200, blank=True)
    ocr_dob = models.CharField(max_length=50, blank=True)
    ocr_aadhaar_number = models.CharField(max_length=50, blank=True)
    ocr_pan_number = models.CharField(max_length=50, blank=True)

    # Consent & Acknowledgement (Strict Privacy Compliance)
    consent_data_processing = models.BooleanField(
        default=True,
        help_text="Explicit user consent for identity verification, safety checks, and minimal data processing"
    )

    # Status & Administrative Review
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    reverification_notes = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_verifications')
    reviewed_at = models.DateTimeField(null=True, blank=True)

    # AI Verification Assistant Structured Output
    ai_outcome = models.CharField(
        max_length=30,
        blank=True,
        choices=[
            ('forward_for_approval', 'Forward for Approval'),
            ('manual_review', 'Manual Review'),
            ('auto_reject', 'Auto Reject'),
        ]
    )
    ai_confidence = models.FloatField(default=0.0)
    ai_checks = models.JSONField(default=dict, blank=True)
    ai_reasoning = models.TextField(blank=True)
    ai_assessment_json = models.JSONField(default=dict, blank=True)
    evaluated_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        outcome_str = f" [AI: {self.ai_outcome}]" if self.ai_outcome else ""
        return f"Verification for {self.user.username} ({self.status}){outcome_str}"

    @property
    def is_verified(self):
        return self.status == 'approved'

    @property
    def masked_document_number(self):
        num = self.document_number or self.ocr_aadhaar_number or self.aadhaar_document_ref
        if not num:
            return "N/A"
        clean = str(num).replace(' ', '').replace('-', '')
        if len(clean) > 4:
            return "X" * (len(clean) - 4) + clean[-4:]
        return clean


class SafetyAssessment(models.Model):
    LIKERT_CHOICES = [
        (1, 'Strongly Disagree'),
        (2, 'Disagree'),
        (3, 'Neither Agree nor Disagree'),
        (4, 'Agree'),
        (5, 'Strongly Agree'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='safety_assessments')
    verification_request = models.ForeignKey(VerificationRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name='safety_assessments')

    # The 6 Standardized Likert Questions
    # Q1: General civic emergency duty
    q1_responsibility = models.IntegerField(
        choices=LIKERT_CHOICES,
        default=5,
        help_text="Q1: I believe everyone has a responsibility to help a person facing a genuine emergency."
    )
    # Q2: Personal willingness to intervene safely
    q2_willingness = models.IntegerField(
        choices=LIKERT_CHOICES,
        default=5,
        help_text="Q2: I would be willing to help someone in an emergency situation when it is safe for me to do so."
    )
    # Q3: Shared community responsibility for women's safety
    q3_shared_safety = models.IntegerField(
        choices=LIKERT_CHOICES,
        default=5,
        help_text="Q3: Women's safety should be treated as a shared responsibility of the entire community."
    )
    # Q4: Personal boundaries and consent
    q4_consent_boundaries = models.IntegerField(
        choices=LIKERT_CHOICES,
        default=5,
        help_text="Q4: I believe respecting personal boundaries and consent is essential for creating a safe environment."
    )
    # Q5: Reporting / seeking official help for incidents
    q5_incident_reporting = models.IntegerField(
        choices=LIKERT_CHOICES,
        default=5,
        help_text="Q5: I would report or seek appropriate help if I witnessed a serious safety incident."
    )
    # Q6: Emergency response confidence and situational awareness
    q6_emergency_confidence = models.IntegerField(
        choices=LIKERT_CHOICES,
        default=5,
        help_text="Q6: I feel confident that I know what to do when someone around me needs emergency assistance."
    )

    # Computed AI Orientation Signals (0.0 to 100.0)
    safety_awareness_score = models.FloatField(default=85.0)
    community_help_score = models.FloatField(default=85.0)
    womens_safety_score = models.FloatField(default=85.0)
    emergency_response_score = models.FloatField(default=85.0)
    responsible_behavior_score = models.FloatField(default=85.0)

    # AI Orientation Summary Text
    ai_summary = models.TextField(blank=True)
    ai_disclaimer = models.TextField(
        default="Advisory Signal Notice: This AI assessment summary evaluates orientation indicators based on survey responses. It does NOT diagnose mental health, morality, criminality, or character. Final verification decisions are made strictly by authorized human administrators."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Safety Assessment for {self.user.username} ({self.created_at.strftime('%Y-%m-%d')})"

    def calculate_scores_and_summary(self):
        """Calculates structured indices and AI advisory summary text."""
        # Convert 1-5 scale into 20-100% scores
        to_pct = lambda val: min(100.0, max(20.0, float(val) * 20.0))

        # 1. Community Help Orientation (Q1 + Q2)
        self.community_help_score = round((to_pct(self.q1_responsibility) + to_pct(self.q2_willingness)) / 2.0, 1)

        # 2. Women's Safety Awareness (Q3 + Q4)
        self.womens_safety_score = round((to_pct(self.q3_shared_safety) + to_pct(self.q4_consent_boundaries)) / 2.0, 1)

        # 3. Emergency Response Awareness (Q5 + Q6)
        self.emergency_response_score = round((to_pct(self.q5_incident_reporting) + to_pct(self.q6_emergency_confidence)) / 2.0, 1)

        # 4. Responsible Behaviour Indicators (Q1 + Q4 + Q5)
        self.responsible_behavior_score = round((to_pct(self.q1_responsibility) + to_pct(self.q4_consent_boundaries) + to_pct(self.q5_incident_reporting)) / 3.0, 1)

        # 5. Overall Safety Awareness
        total_sum = sum([self.q1_responsibility, self.q2_willingness, self.q3_shared_safety, self.q4_consent_boundaries, self.q5_incident_reporting, self.q6_emergency_confidence])
        self.safety_awareness_score = round((total_sum / 30.0) * 100.0, 1)

        # Build descriptive AI summary
        bullets = []
        if self.community_help_score >= 80:
            bullets.append("Demonstrates high readiness to provide civic assistance and cooperate during critical situations.")
        elif self.community_help_score >= 60:
            bullets.append("Displays moderate willingness to assist others when personal safety parameters are established.")
        else:
            bullets.append("Indicates reserved willingness regarding active emergency intervention; suitable for passive alert reception.")

        if self.womens_safety_score >= 80:
            bullets.append("Strongly aligns with shared community safety responsibilities, boundary respect, and active consent principles.")
        else:
            bullets.append("Displays baseline awareness of community safety norms and personal boundary protocols.")

        if self.emergency_response_score >= 80:
            bullets.append("Possesses high confidence in recognizing reporting channels and following emergency guidance.")
        else:
            bullets.append("May benefit from platform-guided emergency action checklists and first-response educational tips.")

        summary_text = (
            f"Orientation Overview: The applicant scores an overall safety awareness index of {self.safety_awareness_score}% "
            f"(Community Help: {self.community_help_score}%, Women's Safety: {self.womens_safety_score}%, "
            f"Emergency Response: {self.emergency_response_score}%, Responsible Behaviour: {self.responsible_behavior_score}%).\n\n"
            + "\n".join(f"• {b}" for b in bullets)
        )
        self.ai_summary = summary_text
        return summary_text


class VerificationAuditLog(models.Model):
    verification_request = models.ForeignKey(VerificationRequest, on_delete=models.CASCADE, related_name='audit_logs')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=50) # 'submitted', 'status_change', 'ai_evaluated', 'note_added', 'police_inspected'
    previous_status = models.CharField(max_length=30, blank=True)
    new_status = models.CharField(max_length=30, blank=True)
    reason = models.TextField(blank=True)
    ip_address = models.CharField(max_length=45, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Audit: {self.action} on Req #{self.verification_request_id} by {self.actor or 'System'}"


class PolicePortalAccessLog(models.Model):
    officer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='police_portal_accesses')
    officer_badge_id = models.CharField(max_length=100, blank=True)
    target_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='police_access_records')
    search_query = models.CharField(max_length=255, blank=True)
    access_purpose = models.TextField(help_text="Official investigative or emergency response purpose")
    data_scope = models.CharField(max_length=100, default="Minimised Verification & Contact Record")
    ip_address = models.CharField(max_length=45, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Police Audit: Officer {self.officer.username} accessed {self.target_user or self.search_query} at {self.timestamp}"
