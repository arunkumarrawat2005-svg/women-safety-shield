from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Location


@login_required
def live_map(request):
    return render(request, 'tracking/live_map.html')


@login_required
def location_history(request):
    locations = Location.objects.filter(user=request.user).order_by('-timestamp')[:50]
    return render(request, 'tracking/history.html', {'locations': locations})


import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from local_residents.models import LocalResident

@csrf_exempt
def heartbeat_location(request):
    """
    Continuous background GPS telemetry update for active authenticated users.
    Synchronizes:
    1. tracking.Location log
    2. local_residents.LocalResident (latitude, longitude, is_available=True)
    """
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)

    lat = None
    lng = None
    acc = None

    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body.decode('utf-8'))
            lat = data.get('latitude') or data.get('lat')
            lng = data.get('longitude') or data.get('lng')
            acc = data.get('accuracy')
        except Exception:
            pass
    if lat is None or lng is None:
        lat = request.POST.get('latitude') or request.POST.get('lat')
        lng = request.POST.get('longitude') or request.POST.get('lng')
        acc = request.POST.get('accuracy')

    try:
        lat = float(lat)
        lng = float(lng)
    except (ValueError, TypeError):
        return JsonResponse({'success': False, 'error': 'Valid coordinates required'}, status=400)

    # 1. Record location breadcrumb
    try:
        Location.objects.create(
            user=request.user,
            latitude=lat,
            longitude=lng,
            accuracy=float(acc) if acc else None
        )
    except Exception:
        pass

    # 2. Sync LocalResident profile so radar and resident directory instantly see real coordinates
    try:
        role = getattr(request.user, 'role', 'user')
        is_verified = bool(request.user.is_verified or request.user.badge_identity_verified or role in ['local_resident', 'guardian', 'volunteer', 'citizen'])
        
        resident, _ = LocalResident.objects.get_or_create(
            user=request.user,
            defaults={
                'local_resident_type': 'citizen' if role == 'user' else (role if role in ['volunteer', 'security', 'ngo', 'citizen'] else 'citizen'),
                'city': request.user.city or 'Delhi NCR',
                'area': request.user.address or request.user.city or 'Central Zone',
                'badge_title': 'Verified Citizen Guardian' if is_verified else 'Community Guardian',
                'is_verified': is_verified,
                'is_available': True,
            }
        )
        resident.latitude = lat
        resident.longitude = lng
        resident.is_available = True
        if is_verified:
            resident.is_verified = True
        resident.save()
    except Exception as e:
        pass

    return JsonResponse({
        'success': True,
        'user': request.user.username,
        'latitude': lat,
        'longitude': lng
    })
