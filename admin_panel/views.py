import functools
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from accounts.models import User
from emergency.models import Emergency
from local_residents.models import LocalResident
from safety_map.models import SafetyReport, SafetyZone
from verification.models import VerificationRequest
from gov_alerts.models import GovAlert
from notifications.models import Notification
from organization.models import Organization


def admin_required(view_func):
    """Decorator ensuring user has staff or admin rights."""
    @login_required
    @functools.wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not (request.user.is_staff or request.user.is_superuser or request.user.role == 'admin'):
            messages.error(request, 'Administrative credentials required to access the Admin Control Center.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


@admin_required
def admin_dashboard(request):
    total_users = User.objects.count()
    active_emergencies = Emergency.objects.filter(status='ACTIVE').count()
    total_emergencies = Emergency.objects.count()
    verified_residents = LocalResident.objects.filter(is_verified=True).count()
    pending_residents = LocalResident.objects.filter(is_verified=False).count()
    total_reports = SafetyReport.objects.count()
    total_zones = SafetyZone.objects.count()
    total_gov_alerts = GovAlert.objects.count()

    recent_emergencies = Emergency.objects.select_related('victim', 'assigned_responder').order_by('-created_at')[:8]
    pending_resident_list = LocalResident.objects.filter(is_verified=False).select_related('user').order_by('-created_at')[:8]
    recent_reports = SafetyReport.objects.select_related('user').order_by('-created_at')[:6]
    recent_gov_alerts = GovAlert.objects.select_related('sos_event').order_by('-sent_at')[:6]

    context = {
        'total_users': total_users,
        'active_emergencies': active_emergencies,
        'total_emergencies': total_emergencies,
        'verified_residents': verified_residents,
        'pending_residents': pending_residents,
        'total_reports': total_reports,
        'total_zones': total_zones,
        'total_gov_alerts': total_gov_alerts,
        # Legacy aliases
        'verified_guardians': verified_residents,
        'pending_guardians': pending_residents,
        'recent_emergencies': recent_emergencies,
        'pending_resident_list': pending_resident_list,
        'pending_guardian_list': pending_resident_list,
        'recent_reports': recent_reports,
        'recent_gov_alerts': recent_gov_alerts,
        'total_organizations': Organization.objects.count(),
        'verified_organizations': Organization.objects.filter(is_verified=True).count(),
        'pending_organizations': Organization.objects.filter(is_verified=False).count(),
    }
    return render(request, 'admin_panel/dashboard.html', context)


# ==================== USER MANAGEMENT ====================
@admin_required
def user_management(request):
    query = request.GET.get('q', '').strip()
    role_filter = request.GET.get('role', '').strip()

    users = User.objects.all().order_by('-date_joined')
    if query:
        users = users.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(phone__icontains=query)
        )
    if role_filter:
        users = users.filter(role=role_filter)

    context = {
        'users': users,
        'query': query,
        'role_filter': role_filter,
        'total_users_count': User.objects.count(),
    }
    return render(request, 'admin_panel/users.html', context)


@admin_required
def admin_toggle_user_active(request, user_id):
    target_user = get_object_or_404(User, pk=user_id)
    if target_user == request.user:
        messages.error(request, "You cannot deactivate your own administrative account.")
        return redirect('admin_users')

    target_user.is_active = not target_user.is_active
    target_user.save()
    status_str = "activated" if target_user.is_active else "deactivated (suspended)"
    messages.success(request, f"User {target_user.username} has been {status_str}.")
    return redirect('admin_users')


@admin_required
def admin_delete_user(request, user_id):
    if request.method == 'POST':
        target_user = get_object_or_404(User, pk=user_id)
        if target_user == request.user:
            messages.error(request, "You cannot delete your own administrative account.")
            return redirect('admin_users')

        uname = target_user.username
        target_user.delete()
        messages.success(request, f"User account '@{uname}' and associated data have been permanently deleted.")
    return redirect('admin_users')


@admin_required
def admin_change_user_role(request, user_id):
    if request.method == 'POST':
        target_user = get_object_or_404(User, pk=user_id)
        new_role = request.POST.get('role')
        if new_role in ['user', 'local_resident', 'organization', 'admin']:
            target_user.role = new_role
            if new_role == 'admin':
                target_user.is_staff = True
            target_user.save()
            messages.success(request, f"Role for @{target_user.username} updated to {new_role}.")
    return redirect('admin_users')


# ==================== EMERGENCY MANAGEMENT ====================
@admin_required
def emergency_management(request):
    status_filter = request.GET.get('status', '').strip()
    query = request.GET.get('q', '').strip()

    emergencies = Emergency.objects.select_related('victim', 'assigned_responder').order_by('-created_at')
    if status_filter:
        emergencies = emergencies.filter(status=status_filter)
    if query:
        emergencies = emergencies.filter(
            Q(victim__username__icontains=query) |
            Q(victim__first_name__icontains=query) |
            Q(victim__last_name__icontains=query) |
            Q(address__icontains=query) |
            Q(id__icontains=query)
        )

    context = {
        'emergencies': emergencies,
        'status_filter': status_filter,
        'query': query,
        'total_count': Emergency.objects.count(),
        'active_count': Emergency.objects.filter(status='ACTIVE').count(),
    }
    return render(request, 'admin_panel/emergencies.html', context)


@admin_required
def admin_close_emergency(request, emergency_id):
    emergency = get_object_or_404(Emergency, pk=emergency_id)
    emergency.status = 'CLOSED'
    emergency.closed_at = timezone.now()
    emergency.save()
    messages.success(request, f"Emergency #{emergency.id} force-closed by administrator.")
    return redirect(request.META.get('HTTP_REFERER', 'admin_emergencies'))


@admin_required
def admin_delete_emergency(request, emergency_id):
    if request.method == 'POST':
        emergency = get_object_or_404(Emergency, pk=emergency_id)
        eid = emergency.id
        emergency.delete()
        messages.success(request, f"Emergency log #{eid} permanently deleted from database.")
    return redirect(request.META.get('HTTP_REFERER', 'admin_emergencies'))


# ==================== LOCAL RESIDENT MANAGEMENT ====================
@admin_required
def resident_management(request):
    status_filter = request.GET.get('status', '').strip()
    residents = LocalResident.objects.select_related('user', 'verified_by').order_by('-created_at')

    if status_filter == 'verified':
        residents = residents.filter(is_verified=True)
    elif status_filter == 'pending':
        residents = residents.filter(is_verified=False)
    elif status_filter == 'available':
        residents = residents.filter(is_verified=True, is_available=True)

    for r in residents:
        r.v_req = VerificationRequest.objects.filter(user=r.user).first()

    context = {
        'residents': residents,
        'status_filter': status_filter,
        'total_residents': LocalResident.objects.count(),
        'verified_count': LocalResident.objects.filter(is_verified=True).count(),
        'pending_count': LocalResident.objects.filter(is_verified=False).count(),
    }
    return render(request, 'admin_panel/residents.html', context)


@admin_required
def verify_resident(request, resident_id):
    resident = get_object_or_404(LocalResident, pk=resident_id)
    resident.is_verified = True
    resident.verified_at = timezone.now()
    resident.verified_by = request.user
    resident.save()

    resident.user.is_verified = True
    resident.user.save()

    v_req = VerificationRequest.objects.filter(user=resident.user, status='pending').first()
    if v_req:
        v_req.status = 'approved'
        v_req.reviewed_by = request.user
        v_req.reviewed_at = timezone.now()
        v_req.save()

    Notification.objects.create(
        recipient=resident.user,
        title="🛡️ Local Resident Approved",
        message="Your Aadhaar/ID verification has been approved by the Admin! You can now toggle availability to receive SOS alerts.",
        notif_type='safety_alert'
    )

    messages.success(request, f"@{resident.user.username} approved as verified Local Resident.")
    return redirect(request.META.get('HTTP_REFERER', 'admin_dashboard'))


verify_guardian = verify_resident


@admin_required
def reject_resident(request, resident_id):
    resident = get_object_or_404(LocalResident, pk=resident_id)
    uname = resident.user.username

    v_req = VerificationRequest.objects.filter(user=resident.user, status='pending').first()
    if v_req:
        v_req.status = 'rejected'
        v_req.admin_notes = 'Document rejected by administrator.'
        v_req.reviewed_by = request.user
        v_req.reviewed_at = timezone.now()
        v_req.save()

    Notification.objects.create(
        recipient=resident.user,
        title="⚠️ ID Verification Rejected",
        message="Your Local Resident application was reviewed and rejected. Please re-upload a clear government-issued ID document.",
        notif_type='safety_alert'
    )

    resident.delete()
    messages.warning(request, f"Resident application for @{uname} rejected and removed.")
    return redirect(request.META.get('HTTP_REFERER', 'admin_dashboard'))


@admin_required
def revoke_resident(request, resident_id):
    resident = get_object_or_404(LocalResident, pk=resident_id)
    resident.is_verified = False
    resident.is_available = False
    resident.save()

    resident.user.is_verified = False
    resident.user.save()

    messages.warning(request, f"Verification revoked for @{resident.user.username}. Responder status set to inactive.")
    return redirect(request.META.get('HTTP_REFERER', 'admin_residents'))


@admin_required
def admin_delete_resident(request, resident_id):
    if request.method == 'POST':
        resident = get_object_or_404(LocalResident, pk=resident_id)
        uname = resident.user.username
        resident.delete()
        messages.success(request, f"Resident responder profile for @{uname} deleted.")
    return redirect('admin_residents')


@admin_required
def admin_update_trust_score(request, resident_id):
    if request.method == 'POST':
        resident = get_object_or_404(LocalResident, pk=resident_id)
        try:
            score = float(request.POST.get('trust_score', 5.0))
            resident.trust_score = max(0.0, min(10.0, round(score, 1)))
            resident.save()
            messages.success(request, f"Trust score for @{resident.user.username} updated to {resident.trust_score}.")
        except ValueError:
            messages.error(request, "Invalid trust score format.")
    return redirect('admin_residents')


# ==================== SAFETY REPORTS MODERATION ====================
@admin_required
def report_management(request):
    reports = SafetyReport.objects.select_related('user').order_by('-created_at')
    cat = request.GET.get('category')
    if cat:
        reports = reports.filter(category=cat)

    context = {
        'reports': reports,
        'categories': SafetyReport.CATEGORY_CHOICES,
        'selected_category': cat,
        'total_reports': SafetyReport.objects.count(),
    }
    return render(request, 'admin_panel/reports.html', context)


@admin_required
def admin_verify_report(request, report_id):
    report = get_object_or_404(SafetyReport, pk=report_id)
    report.is_verified = not report.is_verified
    report.save()
    status_str = "verified" if report.is_verified else "unverified"
    messages.success(request, f"Safety report #{report.id} marked as {status_str}.")
    return redirect('admin_reports')


@admin_required
def admin_delete_report(request, report_id):
    if request.method == 'POST':
        report = get_object_or_404(SafetyReport, pk=report_id)
        rid = report.id
        report.delete()
        messages.success(request, f"Safety report #{rid} permanently deleted.")
    return redirect('admin_reports')


# ==================== SAFETY ZONES & HOTSPOTS ====================
@admin_required
def zone_management(request):
    zones = SafetyZone.objects.all().order_by('-created_at')
    context = {
        'zones': zones,
        'total_zones': zones.count(),
    }
    return render(request, 'admin_panel/zones.html', context)


@admin_required
def admin_create_zone(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        lat = request.POST.get('latitude')
        lng = request.POST.get('longitude')
        radius = request.POST.get('radius_meters', 200)
        status = request.POST.get('status', 'high')
        try:
            SafetyZone.objects.create(
                name=name,
                latitude=float(lat),
                longitude=float(lng),
                radius_meters=int(radius),
                status=status,
                risk_score=8.5 if status == 'high' else 5.0 if status == 'medium' else 1.5
            )
            messages.success(request, f"Safety Zone '{name}' successfully created.")
        except Exception as e:
            messages.error(request, f"Failed to create zone: {str(e)}")
    return redirect('admin_zones')


@admin_required
def admin_delete_zone(request, zone_id):
    if request.method == 'POST':
        zone = get_object_or_404(SafetyZone, pk=zone_id)
        zname = zone.name
        zone.delete()
        messages.success(request, f"Safety zone '{zname}' deleted.")
    return redirect('admin_zones')


# ==================== GOV & POLICE ALERTS ====================
@admin_required
def gov_alerts_log(request):
    alerts = GovAlert.objects.select_related('sos_event', 'sos_event__victim').order_by('-sent_at')
    context = {
        'alerts': alerts,
        'total_alerts': alerts.count(),
    }
    return render(request, 'admin_panel/gov_alerts.html', context)


# ==================== BROADCAST SAFETY ADVISORY ====================
@admin_required
def broadcast_alert(request):
    if request.method == 'POST':
        title = request.POST.get('title', 'Safety Advisory').strip()
        body = request.POST.get('message', '').strip()
        target = request.POST.get('target', 'all')  # 'all' or 'residents'

        if not body:
            messages.error(request, "Broadcast message body cannot be empty.")
            return redirect('admin_dashboard')

        users = User.objects.filter(is_active=True)
        if target == 'residents':
            users = users.filter(role__in=['local_resident', 'guardian'])

        created_count = 0
        for u in users:
            Notification.objects.create(
                recipient=u,
                title=f"🚨 {title}",
                message=body,
                notif_type='safety_alert'
            )
            created_count += 1

        messages.success(request, f"Broadcast successfully dispatched to {created_count} users.")
    return redirect('admin_dashboard')


# ==================== ORGANIZATION GOVERNANCE ====================
@admin_required
def admin_organizations(request):
    status_filter = request.GET.get('status', 'all')
    type_filter = request.GET.get('type', 'all')
    q = request.GET.get('q', '').strip()

    orgs = Organization.objects.select_related('user').prefetch_related('volunteers')

    if status_filter == 'verified':
        orgs = orgs.filter(is_verified=True)
    elif status_filter == 'pending':
        orgs = orgs.filter(is_verified=False)

    if type_filter != 'all' and type_filter:
        orgs = orgs.filter(org_type=type_filter)

    if q:
        orgs = orgs.filter(
            Q(name__icontains=q) |
            Q(address__icontains=q) |
            Q(city__icontains=q) |
            Q(contact_phone__icontains=q) |
            Q(emergency_helpline__icontains=q)
        )

    orgs = orgs.order_by('-created_at')

    context = {
        'organizations': orgs,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'q': q,
        'total_orgs': Organization.objects.count(),
        'verified_orgs': Organization.objects.filter(is_verified=True).count(),
        'pending_orgs': Organization.objects.filter(is_verified=False).count(),
    }
    return render(request, 'admin_panel/organizations.html', context)


@admin_required
def admin_verify_organization(request, org_id):
    org = get_object_or_404(Organization, id=org_id)
    org.is_verified = True
    org.save()
    messages.success(request, f'✅ Organization "{org.name}" verified and accredited successfully.')
    return redirect('admin_organizations')


@admin_required
def admin_revoke_organization(request, org_id):
    org = get_object_or_404(Organization, id=org_id)
    org.is_verified = False
    org.save()
    messages.warning(request, f'⚠️ Organization "{org.name}" verification has been revoked.')
    return redirect('admin_organizations')


@admin_required
def admin_delete_organization(request, org_id):
    org = get_object_or_404(Organization, id=org_id)
    name = org.name
    org.delete()
    messages.info(request, f'Organization "{name}" and its associated records have been deleted.')
    return redirect('admin_organizations')


@admin_required
def admin_verifications(request):
    """Direct route to User Verification Panel."""
    return redirect('admin_verification_dashboard')

