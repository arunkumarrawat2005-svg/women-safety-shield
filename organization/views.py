from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.db.models import Q
import json

from .models import Organization, OrgVolunteer, OrgResponse
from .forms import OrganizationRegistrationForm, OrganizationProfileEditForm, OrgVolunteerAddForm, JoinOrganizationForm
from .services import OrganizationService
from accounts.models import User


def org_list(request):
    """
    Public Organization & Institutional Safety Directory.
    Shows colleges, companies, hospitals, NGOs, and safe haven campuses.
    Accessible to all users before and after login.
    """
    category = request.GET.get('category', 'all')
    query = request.GET.get('q', '').strip()
    city = request.GET.get('city', '').strip()

    organizations = OrganizationService.get_verified_organizations(
        category=category if category != 'all' else None,
        query=query if query else None,
        city=city if city else None
    )

    # Build Map Markers JSON for verified organizations with coordinates
    map_pins = []
    for org in organizations:
        if org.latitude and org.longitude:
            map_pins.append({
                'id': org.id,
                'name': org.name,
                'type': org.get_org_type_display(),
                'type_raw': org.org_type,
                'lat': float(org.latitude),
                'lng': float(org.longitude),
                'address': org.address,
                'city': org.city,
                'hotline': org.hotline_display,
                'badge_class': org.get_badge_class(),
                'icon': org.get_icon(),
                'has_safe_haven': org.has_safe_haven,
                'cctv_monitored': org.cctv_monitored,
                'guards_count': org.security_guards_count,
                'detail_url': f'/organization/{org.id}/'
            })

    total_orgs_count = Organization.objects.filter(is_verified=True).count()
    safe_havens_count = Organization.objects.filter(is_verified=True, has_safe_haven=True).count()
    colleges_count = Organization.objects.filter(is_verified=True, org_type='college').count()
    hospitals_count = Organization.objects.filter(is_verified=True, org_type='hospital').count()

    user_org = None
    if request.user.is_authenticated and hasattr(request.user, 'organization'):
        user_org = request.user.organization

    context = {
        'organizations': organizations,
        'selected_category': category,
        'search_query': query,
        'search_city': city,
        'map_pins_json': json.dumps(map_pins),
        'total_orgs_count': total_orgs_count,
        'safe_havens_count': safe_havens_count,
        'colleges_count': colleges_count,
        'hospitals_count': hospitals_count,
        'user_org': user_org,
    }
    return render(request, 'organization/list.html', context)


def org_detail(request, org_id):
    """
    Detailed Institutional Profile & Safe Haven Campus View.
    """
    org = get_object_or_404(Organization, id=org_id)
    approved_volunteers = org.volunteers.filter(approved_by_org=True).select_related('user')
    available_guards_count = approved_volunteers.filter(is_available=True).count()

    user_is_member = False
    membership_status = None
    if request.user.is_authenticated:
        membership = OrgVolunteer.objects.filter(organization=org, user=request.user).first()
        if membership:
            user_is_member = True
            membership_status = membership.verification_status

    join_form = JoinOrganizationForm()

    context = {
        'organization': org,
        'approved_volunteers': approved_volunteers,
        'available_guards_count': available_guards_count,
        'user_is_member': user_is_member,
        'membership_status': membership_status,
        'join_form': join_form,
    }
    return render(request, 'organization/detail.html', context)


def org_register(request):
    """
    Public Onboarding for Campuses, Corporate Tech Parks, Hospitals & NGOs.
    """
    if request.user.is_authenticated and hasattr(request.user, 'organization'):
        messages.info(request, 'You already have an active organization registered.')
        return redirect('org_dashboard')

    if request.method == 'POST':
        form = OrganizationRegistrationForm(request.POST, user=request.user)
        if form.is_valid():
            if request.user.is_authenticated:
                user = request.user
                user.role = 'organization'
                user.save()
            else:
                user = User.objects.create_user(
                    username=form.cleaned_data['username'],
                    email=form.cleaned_data['contact_email'],
                    password=form.cleaned_data['password'],
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'],
                    phone=form.cleaned_data['contact_phone'],
                    role='organization'
                )
                login(request, user)

            org = form.save(commit=False)
            org.user = user
            org.is_verified = False  # Requires human platform admin approval
            org.save()

            messages.success(
                request,
                f'🎉 Welcome to Women Safety Shield! "{org.name}" has been registered successfully. '
                f'Your campus profile is live and pending admin verification.'
            )
            return redirect('org_dashboard')
        else:
            messages.error(request, 'Please correct the highlighted form errors.')
    else:
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {
                'contact_email': request.user.email,
                'contact_phone': request.user.phone or '',
            }
        form = OrganizationRegistrationForm(initial=initial_data, user=request.user)

    return render(request, 'organization/register.html', {'form': form})


@login_required
def org_dashboard(request):
    """
    Institutional Command Center for Campus Safety & Corporate Security Operations.
    """
    # Allow organization users or system administrators
    if request.user.role != 'organization' and not request.user.is_staff:
        # Check if user has an organization profile
        if hasattr(request.user, 'organization'):
            request.user.role = 'organization'
            request.user.save()
        else:
            messages.info(request, 'Please register your organization to access the Institutional Command Center.')
            return redirect('org_register')

    try:
        org = Organization.objects.get(user=request.user)
    except Organization.DoesNotExist:
        if request.user.is_staff:
            # If admin is viewing, load first organization or prompt
            org = Organization.objects.first()
            if not org:
                messages.warning(request, 'No organizations registered yet. Please create one.')
                return redirect('org_register')
        else:
            messages.warning(request, 'Organization profile not found. Please complete registration.')
            return redirect('org_register')

    # Alerts dispatched within this organization's perimeter
    alerts_qs = OrgResponse.objects.filter(organization=org).select_related(
        'sos_event', 'sos_event__victim', 'volunteer', 'volunteer__user'
    ).order_by('-notified_at')

    active_alerts = alerts_qs.filter(status__in=['notified', 'acknowledged'], sos_event__status='ACTIVE')
    alerts = alerts_qs[:30]

    volunteers = OrgVolunteer.objects.filter(organization=org).select_related('user').order_by('-created_at')
    approved_volunteers = volunteers.filter(approved_by_org=True)
    available_volunteers = approved_volunteers.filter(is_available=True)

    profile_form = OrganizationProfileEditForm(instance=org)
    volunteer_form = OrgVolunteerAddForm()

    context = {
        'organization': org,
        'alerts': alerts,
        'active_alerts': active_alerts,
        'active_alerts_count': active_alerts.count(),
        'volunteers': volunteers,
        'approved_volunteers_count': approved_volunteers.count(),
        'available_volunteers_count': available_volunteers.count(),
        'total_volunteers_count': volunteers.count(),
        'profile_form': profile_form,
        'volunteer_form': volunteer_form,
    }
    return render(request, 'organization/dashboard.html', context)


@login_required
def update_org_profile(request):
    """Update organization campus coordinates, hotline, and amenities."""
    if request.method == 'POST':
        org = get_object_or_404(Organization, user=request.user)
        form = OrganizationProfileEditForm(request.POST, instance=org)
        if form.is_valid():
            form.save()
            messages.success(request, 'Campus security profile updated successfully.')
        else:
            messages.error(request, 'Failed to update profile. Please verify input.')
    return redirect('org_dashboard')


@login_required
def org_join(request, org_id):
    """Apply to join an organization's safety or security team."""
    org = get_object_or_404(Organization, id=org_id)
    if request.method == 'POST':
        form = JoinOrganizationForm(request.POST)
        if form.is_valid():
            role_at_org = form.cleaned_data['role_at_org']
            membership, created = OrgVolunteer.objects.get_or_create(
                organization=org,
                user=request.user,
                defaults={
                    'role_at_org': role_at_org,
                    'approved_by_org': False,
                    'verification_status': 'pending',
                    'is_available': False
                }
            )
            if not created:
                membership.role_at_org = role_at_org
                membership.save()

            messages.success(
                request,
                f'✅ Your application to join {org.name} as a designated responder has been submitted to campus security for approval.'
            )
    return redirect('org_detail', org_id=org.id)


@login_required
def add_org_volunteer(request):
    """Directly add or invite a responder/security guard to organization."""
    org = get_object_or_404(Organization, user=request.user)
    if request.method == 'POST':
        form = OrgVolunteerAddForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username'].strip()
            role_at_org = form.cleaned_data['role_at_org']
            is_available = form.cleaned_data['is_available']

            target_user = User.objects.filter(Q(username=username) | Q(email=username) | Q(phone=username)).first()
            if not target_user:
                messages.error(request, f'No registered user found with username or email: "{username}".')
                return redirect('org_dashboard')

            volunteer, created = OrgVolunteer.objects.get_or_create(
                organization=org,
                user=target_user,
                defaults={
                    'role_at_org': role_at_org,
                    'approved_by_org': True,
                    'verification_status': 'verified',
                    'is_available': is_available
                }
            )
            if not created:
                volunteer.role_at_org = role_at_org
                volunteer.approved_by_org = True
                volunteer.verification_status = 'verified'
                volunteer.is_available = is_available
                volunteer.save()

            messages.success(request, f'✅ {target_user.full_name} enrolled as an approved {volunteer.get_role_at_org_display if hasattr(volunteer, "get_role_at_org_display") else role_at_org}.')
    return redirect('org_dashboard')


@login_required
def approve_volunteer(request, volunteer_id):
    """Approve a responder's application."""
    if request.user.role != 'organization' and not request.user.is_staff:
        return redirect('org_dashboard')

    org = get_object_or_404(Organization, user=request.user) if not request.user.is_staff else None
    if org:
        volunteer = get_object_or_404(OrgVolunteer, id=volunteer_id, organization=org)
    else:
        volunteer = get_object_or_404(OrgVolunteer, id=volunteer_id)

    volunteer.approved_by_org = True
    volunteer.verification_status = 'verified'
    volunteer.is_available = True
    volunteer.save()
    messages.success(request, f'✅ Approved {volunteer.user.full_name} as a designated institutional responder.')
    return redirect('org_dashboard')


@login_required
def reject_volunteer(request, volunteer_id):
    """Reject or remove a volunteer from organization roster."""
    if request.user.role != 'organization' and not request.user.is_staff:
        return redirect('org_dashboard')

    org = get_object_or_404(Organization, user=request.user) if not request.user.is_staff else None
    if org:
        volunteer = get_object_or_404(OrgVolunteer, id=volunteer_id, organization=org)
    else:
        volunteer = get_object_or_404(OrgVolunteer, id=volunteer_id)

    name = volunteer.user.full_name
    volunteer.delete()
    messages.info(request, f'Removed {name} from organization roster.')
    return redirect('org_dashboard')


@login_required
def toggle_volunteer_availability(request, volunteer_id):
    """Toggle guard on-duty / off-duty status."""
    if request.user.role != 'organization' and not request.user.is_staff:
        return redirect('org_dashboard')

    org = get_object_or_404(Organization, user=request.user) if not request.user.is_staff else None
    if org:
        volunteer = get_object_or_404(OrgVolunteer, id=volunteer_id, organization=org)
    else:
        volunteer = get_object_or_404(OrgVolunteer, id=volunteer_id)

    volunteer.is_available = not volunteer.is_available
    volunteer.save()
    status_str = "On-Duty (Available)" if volunteer.is_available else "Off-Duty (Unavailable)"
    messages.success(request, f'{volunteer.user.full_name} is now {status_str}.')
    return redirect('org_dashboard')


@login_required
def assign_org_responder(request, response_id):
    """Assign an on-duty responder to an active SOS alert."""
    if request.method == 'POST':
        org = get_object_or_404(Organization, user=request.user)
        org_response = get_object_or_404(OrgResponse, id=response_id, organization=org)

        volunteer_id = request.POST.get('volunteer_id')
        if volunteer_id:
            volunteer = get_object_or_404(OrgVolunteer, id=volunteer_id, organization=org, approved_by_org=True)
            OrganizationService.assign_responder(org_response, volunteer)
            messages.success(request, f'🚀 Dispatched {volunteer.user.full_name} to SOS #{org_response.sos_event_id}!')
        else:
            messages.error(request, 'Please select a designated responder to dispatch.')

    return redirect('org_dashboard')
