from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.http import JsonResponse
from django.conf import settings
from .models import VerificationRequest, SafetyAssessment, VerificationAuditLog, PolicePortalAccessLog
from .services import DocumentVerificationAssistant, SafetyAssessmentService
from accounts.models import User
from emergency.models import Emergency


def _get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return ip


@login_required
def verification_status(request):
    """
    Citizen Identity Verification & Safety Assessment View.
    Step 2: Upload Government ID document, Live Selfie, and Document Number.
    Step 3: Complete 6-Question Citizen Safety & Awareness Assessment.
    Submits to Verification Queue as 'Pending Review'.
    """
    req = VerificationRequest.objects.filter(user=request.user).first()
    assessment = SafetyAssessment.objects.filter(user=request.user).first()

    if request.method == 'POST':
        doc_type = request.POST.get('document_type', 'aadhaar')
        doc_number = request.POST.get('document_number', '').strip()
        aadhaar_no = request.POST.get('aadhaar_number', '').strip() or doc_number
        pan_no = request.POST.get('pan_number', '').strip().upper()
        
        name_val = request.POST.get('name', '').strip() or request.user.get_full_name()
        dob_val = request.POST.get('dob', '').strip()
        consent_given = request.POST.get('consent_data_processing') in ('on', 'true', '1')

        # File uploads
        doc_file = request.FILES.get('document_file')
        aadhaar_img = request.FILES.get('aadhaar_image') or doc_file or request.FILES.get('document')
        pan_img = request.FILES.get('pan_image')
        selfie_img = request.FILES.get('selfie_image')

        # Save or update VerificationRequest
        if not req:
            req = VerificationRequest.objects.create(
                user=request.user,
                document_type=doc_type,
                document_number=doc_number or aadhaar_no,
                document_file=doc_file,
                aadhaar_document_ref=aadhaar_no,
                additional_documents=aadhaar_img,
                aadhaar_image=aadhaar_img,
                pan_image=pan_img,
                selfie_image=selfie_img,
                ocr_name=name_val,
                ocr_dob=dob_val,
                ocr_aadhaar_number=aadhaar_no,
                ocr_pan_number=pan_no,
                consent_data_processing=consent_given,
                status='pending'
            )
            VerificationAuditLog.objects.create(
                verification_request=req,
                actor=request.user,
                action='submitted',
                previous_status='',
                new_status='pending',
                reason='Initial verification packet submitted by user.',
                ip_address=_get_client_ip(request)
            )
        else:
            req.document_type = doc_type
            if doc_number:
                req.document_number = doc_number
            if doc_file:
                req.document_file = doc_file
            if aadhaar_img:
                req.aadhaar_image = aadhaar_img
                req.additional_documents = aadhaar_img
            if pan_img:
                req.pan_image = pan_img
            if selfie_img:
                req.selfie_image = selfie_img
            if name_val:
                req.ocr_name = name_val
            if dob_val:
                req.ocr_dob = dob_val
            if aadhaar_no:
                req.ocr_aadhaar_number = aadhaar_no
                req.aadhaar_document_ref = aadhaar_no
            if pan_no:
                req.ocr_pan_number = pan_no
            req.consent_data_processing = consent_given
            req.status = 'pending'
            req.save()

            VerificationAuditLog.objects.create(
                verification_request=req,
                actor=request.user,
                action='resubmitted',
                previous_status=req.status,
                new_status='pending',
                reason='Updated verification credentials and documents submitted.',
                ip_address=_get_client_ip(request)
            )

        # Update user date_of_birth if provided
        if dob_val and not request.user.date_of_birth:
            try:
                request.user.date_of_birth = dob_val
                request.user.save(update_fields=['date_of_birth'])
            except Exception:
                pass

        # Execute Document Verification Assistant
        try:
            DocumentVerificationAssistant.evaluate(req)
        except Exception:
            pass

        # Execute Safety Assessment Service (6 Likert Questions)
        has_questions = any(k in request.POST for k in ['q1', 'q2', 'q3', 'q4', 'q5', 'q6'])
        if has_questions:
            try:
                assessment = SafetyAssessmentService.evaluate_and_record(
                    user=request.user,
                    responses=request.POST,
                    verification_request=req
                )
            except Exception:
                pass

        messages.success(
            request,
            'Verification packet submitted successfully! Status set to "Pending Review". '
            'Our administrative officers and automated checks are evaluating your submission.'
        )
        return redirect('verification_status')

    audit_logs = req.audit_logs.all()[:10] if req else []
    return render(request, 'verification/status.html', {
        'verification': req,
        'assessment': assessment,
        'audit_logs': audit_logs,
    })


@user_passes_test(lambda u: u.is_authenticated and (u.is_staff or getattr(u, 'role', '') == 'admin'))
def admin_verification_dashboard(request):
    """
    Dedicated Admin Verification Dashboard.
    Inspects:
    - User profile
    - Document credentials & image previews
    - 6-question safety assessment breakdown & AI orientation scores
    - AI-generated assessment summary & disclaimer
    - Verification audit trail
    - Status actions: Pending -> Under Review -> Verified -> Rejected -> Re-verification Required
    """
    status_filter = request.GET.get('status', '')
    doc_filter = request.GET.get('document_type', '')
    search_q = request.GET.get('q', '').strip()

    queryset = VerificationRequest.objects.select_related('user', 'reviewed_by').prefetch_related('safety_assessments', 'audit_logs').all()

    if status_filter:
        queryset = queryset.filter(status=status_filter)
    if doc_filter:
        queryset = queryset.filter(document_type=doc_filter)
    if search_q:
        queryset = queryset.filter(
            Q(user__username__icontains=search_q) |
            Q(user__first_name__icontains=search_q) |
            Q(user__last_name__icontains=search_q) |
            Q(user__email__icontains=search_q) |
            Q(ocr_name__icontains=search_q) |
            Q(document_number__icontains=search_q)
        )

    # Statistics
    stats = {
        'total': VerificationRequest.objects.count(),
        'pending': VerificationRequest.objects.filter(status='pending').count(),
        'under_review': VerificationRequest.objects.filter(status='under_review').count(),
        'approved': VerificationRequest.objects.filter(status='approved').count(),
        'rejected': VerificationRequest.objects.filter(status='rejected').count(),
        'reverification_required': VerificationRequest.objects.filter(status='reverification_required').count(),
    }

    selected_id = request.GET.get('selected_id')
    selected_req = None
    if selected_id:
        selected_req = queryset.filter(id=selected_id).first()
    if not selected_req and queryset.exists():
        selected_req = queryset.first()

    selected_assessment = None
    if selected_req:
        selected_assessment = SafetyAssessment.objects.filter(user=selected_req.user).first()

    return render(request, 'verification/admin_dashboard.html', {
        'requests': queryset,
        'selected_req': selected_req,
        'selected_assessment': selected_assessment,
        'stats': stats,
        'status_filter': status_filter,
        'doc_filter': doc_filter,
        'search_q': search_q,
    })


@user_passes_test(lambda u: u.is_authenticated and (u.is_staff or getattr(u, 'role', '') == 'admin'))
def admin_verification_action(request, req_id):
    """
    Approve, mark under review, reject, or request re-verification with audit logging.
    """
    req = get_object_or_404(VerificationRequest, id=req_id)
    if request.method == 'POST':
        action = request.POST.get('action')
        reason = request.POST.get('reason', '').strip()
        prev_status = req.status

        if action == 'approve':
            req.status = 'approved'
            req.reviewed_by = request.user
            req.reviewed_at = timezone.now()
            req.notes = reason or 'Approved by administrator.'
            req.save()

            # Mark user verified
            req.user.is_verified = True
            req.user.save(update_fields=['is_verified'])

            # Sync local resident if exists
            from local_residents.models import LocalResident
            LocalResident.objects.filter(user=req.user).update(is_verified=True, verified_at=timezone.now(), verified_by=request.user)

            messages.success(request, f"User @{req.user.username} has been verified successfully.")

        elif action == 'under_review':
            req.status = 'under_review'
            req.notes = reason or 'Moved to active human review.'
            req.save()
            messages.info(request, f"Verification for @{req.user.username} moved to 'Under Review'.")

        elif action == 'reject':
            req.status = 'rejected'
            req.reviewed_by = request.user
            req.reviewed_at = timezone.now()
            req.rejection_reason = reason or 'Document verification failed.'
            req.save()

            req.user.is_verified = False
            req.user.save(update_fields=['is_verified'])

            from local_residents.models import LocalResident
            LocalResident.objects.filter(user=req.user).update(is_verified=False)

            messages.warning(request, f"Verification for @{req.user.username} has been rejected.")

        elif action == 'reverify':
            req.status = 'reverification_required'
            req.reviewed_by = request.user
            req.reviewed_at = timezone.now()
            req.reverification_notes = reason or 'Clearer documents or updated information required.'
            req.save()
            messages.info(request, f"Re-verification requested from @{req.user.username}.")

        # Create audit log entry
        VerificationAuditLog.objects.create(
            verification_request=req,
            actor=request.user,
            action=action,
            previous_status=prev_status,
            new_status=req.status,
            reason=reason,
            ip_address=_get_client_ip(request)
        )

    return redirect(f"/verification/admin/?selected_id={req.id}")


@login_required
def police_portal_view(request):
    """
    Dedicated Government & Police Access Portal.
    Protected by strict Role-Based Access Control (RBAC):
    Only users with role == 'police', is_staff, or superusers may access.
    Implements Data Minimization and Audit Logging.
    """
    if not (request.user.role == 'police' or request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Access Restricted: This portal is reserved strictly for authorized Law Enforcement and Emergency Services personnel.")
        return redirect('home')

    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    view_all = request.GET.get('view', '').strip()
    users_list = []
    selected_user = None

    if query or status_filter or view_all:
        q_filter = Q()
        if query and query.lower() != 'all':
            if query.isdigit():
                q_filter |= Q(id=int(query)) | Q(phone__icontains=query)
            else:
                q_filter |= Q(username__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(email__icontains=query)
        if status_filter == 'verified':
            q_filter &= Q(is_verified=True)
        elif status_filter == 'pending':
            q_filter &= Q(verification_requests__status='pending')
        elif status_filter == 'rejected':
            q_filter &= Q(verification_requests__status='rejected')

        users_list = User.objects.filter(q_filter).distinct().select_related()[:50]

        purpose_val = request.GET.get('purpose', '').strip()
        if not purpose_val:
            if status_filter:
                purpose_val = f"Filtered by Status: {status_filter.capitalize()}"
            elif view_all:
                purpose_val = "Authorized Overview: All Registered Citizens & Responders"
            else:
                purpose_val = "Operational User Lookup / Verification Check"

        # Log search action
        PolicePortalAccessLog.objects.create(
            officer=request.user,
            officer_badge_id=getattr(request.user, 'phone', 'OFFICER-DISPATCH'),
            search_query=f"Search Query: '{query}' | Filter: '{status_filter}' | View: '{view_all}'",
            access_purpose=purpose_val,
            data_scope="Search Summary View (Data Minimized)",
            ip_address=_get_client_ip(request)
        )

    # Detailed view for a specific citizen
    user_id = request.GET.get('user_id')
    if user_id:
        selected_user = User.objects.filter(id=user_id).first()
        if selected_user:
            # Audit log detailed profile access
            PolicePortalAccessLog.objects.create(
                officer=request.user,
                officer_badge_id=getattr(request.user, 'phone', 'OFFICER-DISPATCH'),
                target_user=selected_user,
                search_query=f"Inspected User Profile ID: {selected_user.id}",
                access_purpose=request.GET.get('purpose', 'Emergency Dispatch & Identity Verification Verification'),
                data_scope="Authorized Identification & Emergency Contact Details",
                ip_address=_get_client_ip(request)
            )

    # Portal Overview Metrics
    stats = {
        'total_registered': User.objects.count(),
        'verified_citizens': User.objects.filter(is_verified=True).count(),
        'pending_verifications': VerificationRequest.objects.filter(status='pending').count(),
        'rejected_verifications': VerificationRequest.objects.filter(status='rejected').count(),
        'active_emergencies': Emergency.objects.filter(status='ACTIVE').count(),
        'total_emergencies': Emergency.objects.count(),
    }

    # Recent Audit Logs for this officer
    officer_logs = PolicePortalAccessLog.objects.filter(officer=request.user).order_by('-timestamp')[:10]

    return render(request, 'verification/police_portal.html', {
        'stats': stats,
        'users_list': users_list,
        'selected_user': selected_user,
        'query': query,
        'status_filter': status_filter,
        'view_all': view_all,
        'officer_logs': officer_logs,
    })


@login_required
def police_log_access(request):
    """API endpoint to record justified audit logs on sensitive field access."""
    if not (request.user.role == 'police' or request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'status': 'forbidden'}, status=403)

    if request.method == 'POST':
        target_user_id = request.POST.get('target_user_id')
        purpose = request.POST.get('purpose', 'Authorized Emergency Response')
        target_user = User.objects.filter(id=target_user_id).first()

        PolicePortalAccessLog.objects.create(
            officer=request.user,
            officer_badge_id=getattr(request.user, 'phone', 'OFFICER'),
            target_user=target_user,
            search_query=f"Explicit Field Inspection on User #{target_user_id}",
            access_purpose=purpose,
            data_scope="Emergency Location / Verified Responder Attributes",
            ip_address=_get_client_ip(request)
        )
        return JsonResponse({'status': 'logged'})
    return JsonResponse({'status': 'invalid'}, status=400)
