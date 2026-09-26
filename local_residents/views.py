import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg, Sum
from .models import LocalResident, SafeEscortRequest
from .forms import LocalResidentRegistrationForm


@login_required
def resident_register(request):
    resident = LocalResident.objects.filter(user=request.user).first()
    if resident:
        if not request.user.can_act_as_helper or not resident.is_verified:
            messages.info(
                request,
                'You are registered as a Local Resident! Please complete your Identity Verification & Safety Assessment to activate responder privileges.'
            )
            return redirect('verification_status')
        return redirect('resident_profile')

    form = LocalResidentRegistrationForm()
    if request.method == 'POST':
        form = LocalResidentRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            resident = form.save(commit=False)
            resident.user = request.user
            is_user_already_verified = bool(request.user.is_verified or request.user.badge_identity_verified)
            resident.is_verified = is_user_already_verified
            resident.is_available = is_user_already_verified
            resident.save()
            request.user.role = 'local_resident'
            request.user.save(update_fields=['role'])
            if is_user_already_verified:
                messages.success(
                    request,
                    'Welcome to the Local Guardian network! Your verified identity has activated your community responder privileges.'
                )
                return redirect('resident_profile')
            else:
                messages.success(
                    request,
                    'Application Submitted! Please complete your Identity Verification & Safety Assessment to activate your community guardian badge.'
                )
                return redirect('verification_status')

    return render(request, 'local_residents/register.html', {'form': form})


guardian_register = resident_register


@login_required
def resident_profile(request):
    resident = LocalResident.objects.filter(user=request.user).first()
    if not resident:
        messages.info(request, 'Please register your Local Resident profile first.')
        return redirect('resident_register')
    return render(request, 'local_residents/profile.html', {'resident': resident, 'guardian': resident})


guardian_profile = resident_profile


@login_required
def toggle_availability(request):
    resident = LocalResident.objects.filter(user=request.user).first()
    next_url = request.GET.get('next') or request.META.get('HTTP_REFERER') or 'resident_profile'
    if not resident:
        messages.error(request, 'You need to register as a Local Resident first.')
        return redirect('resident_register')

    if not request.user.can_act_as_helper or not resident.is_verified:
        messages.warning(
            request,
            'Community Helper Restriction: Only verified community guardians can activate active responder availability. '
            'Please complete Step 2 Identity Verification & await admin approval.'
        )
        return redirect('verification_status')

    resident.is_available = not resident.is_available
    resident.save()
    status = 'available' if resident.is_available else 'unavailable'
    messages.success(request, f'You are now {status}.')
    return redirect(next_url)



@login_required
def update_location(request):
    next_url = request.POST.get('next') or request.GET.get('next') or request.META.get('HTTP_REFERER') or 'resident_profile'
    if request.method == 'POST':
        resident = LocalResident.objects.filter(user=request.user).first()
        if not resident:
            messages.error(request, 'Local Resident profile not found.')
            return redirect('resident_register')
        resident.latitude = request.POST.get('latitude')
        resident.longitude = request.POST.get('longitude')
        resident.save()
        messages.success(request, 'Your location has been updated.')
        return redirect(next_url)
    return redirect(next_url)


def resident_list(request):
    # Ensure verified local community guardians exist in database
    if LocalResident.objects.filter(is_verified=True).count() < 6:
        try:
            from .seed_data import seed_verified_residents
            seed_verified_residents()
        except Exception:
            pass

    residents_qs = LocalResident.objects.filter(is_verified=True).select_related('user')

    # Parse GPS coordinates if supplied
    user_lat = None
    user_lng = None
    try:
        if request.GET.get('lat') and request.GET.get('lng'):
            user_lat = float(request.GET.get('lat'))
            user_lng = float(request.GET.get('lng'))
    except (ValueError, TypeError):
        user_lat = None
        user_lng = None

    # Search filter
    q = request.GET.get('q', '').strip()
    if q:
        residents_qs = residents_qs.filter(
            Q(user__first_name__icontains=q) |
            Q(user__last_name__icontains=q) |
            Q(user__username__icontains=q) |
            Q(organization_name__icontains=q) |
            Q(area__icontains=q) |
            Q(city__icontains=q) |
            Q(skills__icontains=q) |
            Q(description__icontains=q)
        )

    # Type filter
    resident_type = request.GET.get('type', '').strip()
    if resident_type and resident_type != 'all':
        residents_qs = residents_qs.filter(local_resident_type=resident_type)

    # Availability filter
    availability = request.GET.get('availability', '').strip()
    if availability == 'available':
        residents_qs = residents_qs.filter(is_available=True)
    elif availability == 'offline':
        residents_qs = residents_qs.filter(is_available=False)

    # City filter
    city = request.GET.get('city', '').strip()
    if city and city != 'all':
        residents_qs = residents_qs.filter(city__icontains=city)

    # Aggregate stats
    total_verified = LocalResident.objects.filter(is_verified=True).count()
    available_count = LocalResident.objects.filter(is_verified=True, is_available=True).count()
    total_responses_agg = LocalResident.objects.filter(is_verified=True).aggregate(Sum('successful_responses'))['successful_responses__sum'] or 0
    avg_trust = LocalResident.objects.filter(is_verified=True).aggregate(Avg('trust_score'))['trust_score__avg'] or 9.6

    # Distinct fallback offsets for visual distribution if exact coords not set
    coords_fallback = [
        (28.5494, 77.2001, "Hauz Khas / South Campus"),
        (28.6904, 77.2074, "North Campus / DU"),
        (28.6315, 77.2167, "Connaught Place / Central"),
        (28.6280, 77.3649, "Noida Sector 62"),
        (28.4950, 77.0895, "Gurugram DLF"),
        (28.5700, 77.3200, "Mayur Vihar"),
    ]

    import math
    def haversine(lat1, lon1, lat2, lon2):
        r = 6371.0
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = (math.sin(d_lat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(d_lon / 2) ** 2)
        return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Map radar JSON serialization & Distance Calculation
    map_residents = []
    residents_list = list(residents_qs)

    for idx, r in enumerate(residents_list):
        fb_lat, fb_lng, fb_area = coords_fallback[idx % len(coords_fallback)]
        lat = r.latitude if r.latitude else fb_lat
        lng = r.longitude if r.longitude else fb_lng
        area = r.area if (r.area and r.area != 'Central Zone') else fb_area

        dist_km = None
        dist_text = None
        eta_mins = None
        is_nearby = False

        if user_lat is not None and user_lng is not None:
            dist_val = haversine(user_lat, user_lng, lat, lng)
            dist_km = round(dist_val, 2)
            dist_text = f"{int(dist_val * 1000)} m" if dist_val < 1.0 else f"{dist_val:.1f} km"
            eta_mins = max(1, int(round((dist_val / 4.5) * 60)))
            is_nearby = dist_val <= 3.0
            r.distance_km = dist_km
            r.distance_text = dist_text
            r.eta_mins = eta_mins
            r.is_nearby = is_nearby

        map_residents.append({
            'id': r.id,
            'name': r.user.full_name or r.user.username,
            'username': r.user.username,
            'type': r.get_local_resident_type_display(),
            'type_key': r.local_resident_type,
            'trust_score': round(float(r.trust_score), 1),
            'is_available': r.is_available,
            'lat': float(lat),
            'lng': float(lng),
            'area': area,
            'city': r.city or "Delhi NCR",
            'skills': ", ".join(r.skill_list),
            'badge': r.badge_title or "Community Guardian",
            'responses': r.successful_responses,
            'avatar': (r.user.first_name[0] if r.user.first_name else r.user.username[0]).upper(),
            'distance_km': dist_km,
            'distance_text': dist_text,
            'eta_mins': eta_mins,
            'is_nearby': is_nearby,
        })

    # If user coordinates are provided, sort closest guardians first
    if user_lat is not None and user_lng is not None:
        residents_list.sort(key=lambda x: (getattr(x, 'distance_km', 9999), -getattr(x, 'trust_score', 0)))
        map_residents.sort(key=lambda x: (x['distance_km'] if x['distance_km'] is not None else 9999, -x['trust_score']))

    # Escort requests for current user
    user_escorts = []
    if request.user.is_authenticated:
        user_escorts = SafeEscortRequest.objects.filter(requester=request.user)[:5]

    return render(request, 'local_residents/list.html', {
        'residents': residents_list,
        'guardians': residents_list,
        'residents_json': json.dumps(map_residents),
        'total_verified': total_verified,
        'available_count': available_count,
        'total_responses': total_responses_agg,
        'avg_trust': round(avg_trust, 1),
        'q': q,
        'selected_type': resident_type,
        'selected_avail': availability,
        'selected_city': city,
        'user_escorts': user_escorts,
        'type_choices': LocalResident.LOCAL_RESIDENT_TYPE_CHOICES,
        'user_lat': user_lat,
        'user_lng': user_lng,
    })


guardian_list = resident_list


@login_required
def request_safe_escort(request):
    if request.method == 'POST':
        pickup = request.POST.get('pickup_location', '').strip()
        destination = request.POST.get('destination', '').strip()
        scheduled_time = request.POST.get('scheduled_time', 'Immediate')
        note = request.POST.get('note', '').strip()
        resident_id = request.POST.get('resident_id')

        if not pickup or not destination:
            messages.error(request, 'Pickup location and destination are required.')
            return redirect('resident_list')

        assigned_resident = None
        if resident_id:
            assigned_resident = LocalResident.objects.filter(id=resident_id, is_verified=True).first()

        req = SafeEscortRequest.objects.create(
            requester=request.user,
            resident=assigned_resident,
            pickup_location=pickup,
            destination=destination,
            scheduled_time=scheduled_time,
            note=note,
            status='pending'
        )

        user_name = request.user.full_name or request.user.username
        from notifications.models import Notification
        if assigned_resident:
            Notification.objects.create(
                recipient=assigned_resident.user,
                title="🚶‍♀️ Safe Walk Escort Request",
                message=f"{user_name} requested safe accompaniment from {pickup} to {destination} ({scheduled_time}).",
                notif_type='info'
            )
        else:
            available_residents = LocalResident.objects.filter(is_verified=True, is_available=True)
            for res in available_residents[:5]:
                Notification.objects.create(
                    recipient=res.user,
                    title="🚶‍♀️ Safe Walk Escort Broadcast",
                    message=f"Community alert: {user_name} requested a safe walk escort from {pickup} to {destination}.",
                    notif_type='info'
                )

        messages.success(request, f'🚶‍♀️ Safe Walk escort request #{req.id} submitted! Verified community guardians have been alerted.')
    return redirect('resident_list')


@login_required
def respond_safe_escort(request, pk):
    escort = get_object_or_404(SafeEscortRequest, pk=pk)
    action = request.POST.get('action') or request.GET.get('action')
    resident = LocalResident.objects.filter(user=request.user).first()

    if action == 'accept':
        if not request.user.can_act_as_helper or not resident or not resident.is_verified:
            messages.error(
                request,
                "Permission Denied: Only verified community helpers can accept safe escort requests. "
                "Basic Users can request assistance, but must complete identity verification to accompany others."
            )
            return redirect('resident_list')
        escort.resident = resident
        escort.status = 'accepted'

        escort.save()
        from notifications.models import Notification
        Notification.objects.create(
            recipient=escort.requester,
            title="✅ Escort Request Accepted",
            message=f"Verified responder {resident.user.full_name} accepted your escort request. Meeting at: {escort.pickup_location}.",
            notif_type='info'
        )
        messages.success(request, f"You have accepted the escort request for {escort.requester.full_name}.")
    elif action == 'complete' and (escort.requester == request.user or (resident and escort.resident == resident)):
        escort.status = 'completed'
        escort.save()
        if escort.resident:
            escort.resident.successful_responses += 1
            escort.resident.update_trust_score()
        messages.success(request, "Safe Walk Escort marked as completed. Thank you for keeping the community safe!")
    elif action == 'cancel' and escort.requester == request.user:
        escort.status = 'cancelled'
        escort.save()
        messages.info(request, "Escort request cancelled.")

    return redirect('resident_list')

