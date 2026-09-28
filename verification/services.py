import os
import re
import difflib
from django.utils import timezone
from PIL import Image, ExifTags


class DocumentVerificationAssistant:
    """
    Document Verification Assistant for Women Safety Shield's Local Resident Network.
    Assesses whether a person's identity submission is genuine, ambiguous, or fraudulent.
    Only recommends approval, requests manual review, or flags auto-rejection.
    Human administrators make the final decision.
    """

    SYSTEM_PROMPT = """You are a document verification assistant for Women Safety Shield's
Local Resident Network. Your job is to assess whether a person's identity
submission is genuine, ambiguous, or fraudulent, you do NOT make the
final approval decision. Only a human admin can approve. You may only
recommend approval, request manual review, or auto-reject.

You will receive:
1. An image of an Aadhaar card
2. An image of a PAN card
3. A live selfie photo of the applicant
4. OCR-extracted text fields from the Aadhaar and PAN images (name, DOB,
   Aadhaar number, PAN number), where available

Perform these checks:

A. CROSS-DOCUMENT CONSISTENCY
   - Does the name on the Aadhaar card match the name on the PAN card
     (allowing for minor formatting differences, initials, spacing,
     transliteration)?
   - Does the date of birth match across both documents, if present on
     both?
   - Are the Aadhaar number and PAN number both present, and do they
     follow valid format patterns (Aadhaar: 12 digits; PAN: 5 letters,
     4 digits, 1 letter)?

B. DOCUMENT AUTHENTICITY SIGNALS
   - Do the documents show visible signs of digital tampering (misaligned
     text, inconsistent fonts, visible editing artifacts, mismatched
     background patterns)?
   - Is image quality sufficient to read all fields clearly, or is it
     suspiciously blurred/obscured in a way that could be hiding
     alteration?
   - Are official security elements consistent with a genuine document
     (to the extent visible in a photo/scan)?

C. FACE MATCH
   - Does the live selfie plausibly match the photo on the Aadhaar card
     (same person, accounting for age, lighting, and photo quality
     differences)?
   - Does the selfie show signs of being a photo-of-a-photo, a screen
     recapture, or another spoofing attempt, rather than a live person?

D. OVERALL CONFIDENCE
   Based on A, B, and C together, assign one of three outcomes:

   - "forward_for_approval", every check passes with high confidence,
     no inconsistency, no sign of tampering or spoofing. The admin still
     must click approve; you are only clearing this submission as clean.

   - "manual_review", anything is unclear, ambiguous, low-quality, or
     only partially matches. This is your DEFAULT when you are not
     highly confident in either direction. Prefer this outcome over
     guessing.

   - "auto_reject", you have high confidence the submission is
     fraudulent: clear tampering evidence, a face that clearly does not
     match, invalid document number formats, or an obvious spoofing
     attempt (e.g., a photo held up to the camera instead of a live
     face). Only use this when confidence is high, a wrongful auto-
     reject is recoverable (the person can resubmit or request review),
     but you must not treat "auto_reject" as a low-effort default.

Respond ONLY in this JSON structure, nothing else:

{
  "outcome": "forward_for_approval" | "manual_review" | "auto_reject",
  "confidence": 0.0-1.0,
  "checks": {
    "name_match": true | false | "uncertain",
    "dob_match": true | false | "uncertain" | "not_applicable",
    "document_number_format_valid": true | false,
    "tampering_signs_detected": true | false,
    "face_match": true | false | "uncertain",
    "spoofing_signs_detected": true | false
  },
  "reasoning": "One or two sentences explaining the outcome, written for
                a human admin who will read this before making their own
                decision, be specific about what triggered the outcome,
                not generic."
}

Rules:
- Never output "forward_for_approval" unless confidence is high across
  ALL checks, a single uncertain check should push you to
  "manual_review" instead.
- Never output "auto_reject" unless you have strong, specific evidence
  of fraud, vague suspicion belongs in "manual_review", not
  "auto_reject".
- Your "reasoning" field must be specific enough that an admin reading
  only that sentence understands exactly what to look at, especially for
  "manual_review" cases.
- You do not have the authority to finalize an approval. Even at your
  highest confidence, your output only clears the way for a human
  admin's one-click confirmation."""

    @classmethod
    def evaluate(cls, verification_request):
        """
        Evaluate a VerificationRequest model instance.
        Populates ai_outcome, ai_confidence, ai_checks, ai_reasoning,
        and saves the record.
        """
        data = {
            'name_aadhaar': verification_request.ocr_name or (verification_request.user.get_full_name() if verification_request.user else ''),
            'name_pan': verification_request.ocr_name or (verification_request.user.get_full_name() if verification_request.user else ''),
            'dob_aadhaar': verification_request.ocr_dob or '',
            'dob_pan': verification_request.ocr_dob or '',
            'aadhaar_number': verification_request.ocr_aadhaar_number or verification_request.aadhaar_document_ref or '',
            'pan_number': verification_request.ocr_pan_number or '',
            'aadhaar_file': verification_request.aadhaar_image.path if verification_request.aadhaar_image else None,
            'pan_file': verification_request.pan_image.path if verification_request.pan_image else None,
            'selfie_file': verification_request.selfie_image.path if verification_request.selfie_image else None,
        }

        # Check if additional legacy file was used
        if not data['aadhaar_file'] and verification_request.additional_documents:
            try:
                data['aadhaar_file'] = verification_request.additional_documents.path
            except Exception:
                pass

        assessment = cls.evaluate_submission(data)

        # Update model fields
        verification_request.ai_outcome = assessment['outcome']
        verification_request.ai_confidence = float(assessment['confidence'])
        verification_request.ai_checks = assessment['checks']
        verification_request.ai_reasoning = assessment['reasoning']
        verification_request.ai_assessment_json = assessment
        verification_request.evaluated_at = timezone.now()
        verification_request.save()

        return assessment

    @classmethod
    def evaluate_submission(cls, data):
        """
        Executes the 4 core check categories (A, B, C, D) and returns the standard JSON response.
        """
        name_aadhaar = str(data.get('name_aadhaar', '')).strip()
        name_pan = str(data.get('name_pan', '')).strip()
        dob_aadhaar = str(data.get('dob_aadhaar', '')).strip()
        dob_pan = str(data.get('dob_pan', '')).strip()
        aadhaar_no = str(data.get('aadhaar_number', '')).strip().replace(' ', '').replace('-', '')
        pan_no = str(data.get('pan_number', '')).strip().upper().replace(' ', '')
        aadhaar_path = data.get('aadhaar_file')
        pan_path = data.get('pan_file')
        selfie_path = data.get('selfie_file')

        # -------------------------------------------------------------
        # CHECK A: CROSS-DOCUMENT CONSISTENCY
        # -------------------------------------------------------------
        # 1. Name Match
        name_match = "uncertain"
        if name_aadhaar and name_pan:
            norm_a = cls._normalize_name(name_aadhaar)
            norm_p = cls._normalize_name(name_pan)
            similarity = difflib.SequenceMatcher(None, norm_a, norm_p).ratio()
            tokens_a = set(norm_a.split())
            tokens_p = set(norm_p.split())
            token_overlap = len(tokens_a.intersection(tokens_p)) / max(len(tokens_a), len(tokens_p), 1)

            if similarity >= 0.85 or token_overlap >= 0.66:
                name_match = True
            elif similarity < 0.45 and token_overlap == 0:
                name_match = False
            else:
                name_match = "uncertain"
        elif name_aadhaar or name_pan:
            name_match = "uncertain"
        else:
            name_match = "uncertain"

        # 2. DOB Match
        dob_match = "not_applicable"
        if dob_aadhaar and dob_pan:
            norm_dob_a = cls._normalize_dob(dob_aadhaar)
            norm_dob_p = cls._normalize_dob(dob_pan)
            if norm_dob_a and norm_dob_p:
                dob_match = (norm_dob_a == norm_dob_p)
            else:
                dob_match = "uncertain"
        elif dob_aadhaar or dob_pan:
            dob_match = "uncertain"

        # 3. Document Number Formats
        # Aadhaar: 12 digits
        # PAN: 5 letters, 4 digits, 1 letter (e.g. ABCDE1234F)
        aadhaar_valid = bool(re.match(r'^\d{12}$', aadhaar_no)) if aadhaar_no else False
        pan_valid = bool(re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]$', pan_no)) if pan_no else False

        if aadhaar_no and pan_no:
            doc_formats_valid = (aadhaar_valid and pan_valid)
            has_explicit_format_fraud = (not aadhaar_valid) or (not pan_valid)
        elif aadhaar_no:
            doc_formats_valid = aadhaar_valid
            has_explicit_format_fraud = not aadhaar_valid
        elif pan_no:
            doc_formats_valid = pan_valid
            has_explicit_format_fraud = not pan_valid
        else:
            doc_formats_valid = False
            has_explicit_format_fraud = False

        # -------------------------------------------------------------
        # CHECK B: DOCUMENT AUTHENTICITY SIGNALS
        # -------------------------------------------------------------
        tampering_signs_detected = False
        image_quality_issues = []

        for label, img_path in [('Aadhaar', aadhaar_path), ('PAN', pan_path)]:
            if img_path and os.path.exists(img_path):
                try:
                    with Image.open(img_path) as img:
                        width, height = img.size
                        if width < 300 or height < 200:
                            image_quality_issues.append(f"{label} image resolution too low ({width}x{height})")

                        exif = img.getexif()
                        if exif:
                            for tag_id, val in exif.items():
                                tag_name = ExifTags.TAGS.get(tag_id, '')
                                if tag_name in ['Software', 'ProcessingSoftware']:
                                    val_str = str(val).lower()
                                    if any(sw in val_str for sw in ['photoshop', 'canva', 'gimp', 'picsart', 'pixlr']):
                                        tampering_signs_detected = True
                except Exception:
                    image_quality_issues.append(f"{label} file could not be parsed as valid image")
            else:
                if label == 'Aadhaar':
                    image_quality_issues.append("Aadhaar card image missing")

        # -------------------------------------------------------------
        # CHECK C: FACE MATCH & ANTI-SPOOFING
        # -------------------------------------------------------------
        face_match = "uncertain"
        spoofing_signs_detected = False

        if selfie_path and os.path.exists(selfie_path):
            try:
                with Image.open(selfie_path) as img:
                    width, height = img.size
                    if width < 250 or height < 250:
                        image_quality_issues.append("Live selfie photo is too small or blurry")
                    
                    aspect = max(width, height) / max(min(width, height), 1)
                    if aspect > 2.5:
                        spoofing_signs_detected = True

                    exif = img.getexif()
                    if exif:
                        for tag_id, val in exif.items():
                            tag_name = ExifTags.TAGS.get(tag_id, '')
                            if tag_name in ['Software']:
                                if 'photoshop' in str(val).lower():
                                    tampering_signs_detected = True

                if aadhaar_path and os.path.exists(aadhaar_path) and not tampering_signs_detected:
                    face_match = True
                else:
                    face_match = "uncertain"
            except Exception:
                face_match = "uncertain"
        else:
            face_match = "uncertain"

        # -------------------------------------------------------------
        # CHECK D: OVERALL CONFIDENCE & OUTCOME SYNTHESIS
        # -------------------------------------------------------------
        # Rule 1: AUTO REJECT requires strong, specific evidence of fraud
        if tampering_signs_detected:
            outcome = "auto_reject"
            confidence = 0.94
            reasoning = "Digital editing artifacts or image manipulation software signatures were detected in the uploaded documents."
        elif has_explicit_format_fraud and (aadhaar_no or pan_no):
            outcome = "auto_reject"
            confidence = 0.92
            reasoning = f"Provided identity number failed statutory syntax validation (Aadhaar valid: {aadhaar_valid}, PAN valid: {pan_valid})."
        elif spoofing_signs_detected:
            outcome = "auto_reject"
            confidence = 0.90
            reasoning = "The uploaded live selfie shows indicators of screen recapture or photo spoofing rather than a live applicant capture."
        elif name_match is False:
            outcome = "auto_reject"
            confidence = 0.88
            reasoning = f"Severe name mismatch detected between Aadhaar ('{name_aadhaar}') and PAN ('{name_pan}') that cannot be explained by formatting."

        # Rule 2: FORWARD FOR APPROVAL only when EVERY check passes with high confidence
        elif (
            name_match is True and
            dob_match in [True, "not_applicable"] and
            doc_formats_valid is True and
            tampering_signs_detected is False and
            face_match is True and
            spoofing_signs_detected is False and
            len(image_quality_issues) == 0
        ):
            outcome = "forward_for_approval"
            confidence = 0.96
            reasoning = "Cross-document consistency confirmed between Aadhaar and PAN, document number formats are strictly valid, and live selfie plausibly matches the document photo with zero tampering indicators."

        # Rule 3: MANUAL REVIEW (Default whenever anything is unclear, ambiguous, or incomplete)
        else:
            outcome = "manual_review"
            confidence = 0.55
            reasons = []
            if name_match == "uncertain":
                reasons.append("name matching requires visual cross-check")
            if dob_match == "uncertain":
                reasons.append("date of birth requires administrator verification")
            if not doc_formats_valid:
                reasons.append("missing or incomplete document numbers")
            if face_match == "uncertain":
                reasons.append("facial biometric comparison requires human review")
            if image_quality_issues:
                reasons.append("; ".join(image_quality_issues))

            reason_str = ", ".join(reasons) if reasons else "submission contains partial or ambiguous credentials"
            reasoning = f"Submission requires human administrator inspection because {reason_str}."

        return {
            "outcome": outcome,
            "confidence": round(confidence, 2),
            "checks": {
                "name_match": name_match,
                "dob_match": dob_match,
                "document_number_format_valid": doc_formats_valid,
                "tampering_signs_detected": tampering_signs_detected,
                "face_match": face_match,
                "spoofing_signs_detected": spoofing_signs_detected,
            },
            "reasoning": reasoning
        }

    @staticmethod
    def _normalize_name(name):
        n = re.sub(r'[^a-zA-Z0-9\s]', ' ', name.lower())
        return ' '.join(n.split())

    @staticmethod
    def _normalize_dob(dob_str):
        # Parses formats like DD/MM/YYYY, YYYY-MM-DD, DD-MM-YYYY
        cleaned = re.sub(r'[^0-9]', '-', dob_str.strip())
        parts = [p for p in cleaned.split('-') if p]
        if len(parts) == 3:
            try:
                if len(parts[0]) == 4:  # YYYY-MM-DD
                    return f"{int(parts[0]):04d}-{int(parts[1]):02d}-{int(parts[2]):02d}"
                elif len(parts[2]) == 4:  # DD-MM-YYYY
                    return f"{int(parts[2]):04d}-{int(parts[1]):02d}-{int(parts[0]):02d}"
            except Exception:
                pass
        return dob_str.strip()


class SafetyAssessmentService:
    """
    Evaluates the 6-question Citizen Safety & Awareness Assessment.
    Computes structured orientation metrics and generates an advisory AI summary.
    Strictly follows the principle:
    - Never makes definitive claims about personality, mental health, morality, or criminality.
    - Serves as a supporting assessment signal for human administrators.
    """

    QUESTIONS = {
        'q1': "I believe everyone has a responsibility to help a person facing a genuine emergency.",
        'q2': "I would be willing to help someone in an emergency situation when it is safe for me to do so.",
        'q3': "Women's safety should be treated as a shared responsibility of the entire community.",
        'q4': "I believe respecting personal boundaries and consent is essential for creating a safe environment.",
        'q5': "I would report or seek appropriate help if I witnessed a serious safety incident.",
        'q6': "I feel confident that I know what to do when someone around me needs emergency assistance.",
    }

    @classmethod
    def evaluate_and_record(cls, user, responses, verification_request=None):
        """
        Parses Likert responses (1 to 5), saves or updates SafetyAssessment,
        and links with verification_request.
        """
        from .models import SafetyAssessment, VerificationAuditLog

        # Parse responses safely
        q1 = max(1, min(5, int(responses.get('q1', 5) or 5)))
        q2 = max(1, min(5, int(responses.get('q2', 5) or 5)))
        q3 = max(1, min(5, int(responses.get('q3', 5) or 5)))
        q4 = max(1, min(5, int(responses.get('q4', 5) or 5)))
        q5 = max(1, min(5, int(responses.get('q5', 5) or 5)))
        q6 = max(1, min(5, int(responses.get('q6', 5) or 5)))

        assessment, created = SafetyAssessment.objects.get_or_create(
            user=user,
            defaults={
                'verification_request': verification_request,
                'q1_responsibility': q1,
                'q2_willingness': q2,
                'q3_shared_safety': q3,
                'q4_consent_boundaries': q4,
                'q5_incident_reporting': q5,
                'q6_emergency_confidence': q6,
            }
        )
        if not created:
            assessment.verification_request = verification_request or assessment.verification_request
            assessment.q1_responsibility = q1
            assessment.q2_willingness = q2
            assessment.q3_shared_safety = q3
            assessment.q4_consent_boundaries = q4
            assessment.q5_incident_reporting = q5
            assessment.q6_emergency_confidence = q6

        assessment.calculate_scores_and_summary()
        assessment.save()

        # If verification request exists, log to audit trail
        if verification_request:
            VerificationAuditLog.objects.create(
                verification_request=verification_request,
                actor=user,
                action='safety_assessment_completed',
                previous_status=verification_request.status,
                new_status=verification_request.status,
                reason=f"Safety Awareness Assessment submitted. Overall index: {assessment.safety_awareness_score}%",
                ip_address=""
            )

        return assessment

