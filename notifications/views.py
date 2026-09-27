from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Notification
import json



@login_required
def notification_list(request):
    notifications = Notification.objects.filter(recipient=request.user)[:30]
    return render(request, 'notifications/list.html', {'notifications': notifications})

@login_required
def mark_read(request, pk):
    Notification.objects.filter(pk=pk, recipient=request.user).update(is_read=True)
    return JsonResponse({'success': True})

@login_required
def mark_all_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'success': True})


from django.http import JsonResponse as JR
from django.contrib.auth.decorators import login_required as lr

@lr
def notification_count(request):
    from .models import Notification
    count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return JR({'count': count})

@login_required
def save_token(request):
    try:
        data = json.loads(request.body.decode('utf-8') or '{}')
        token = data.get("token")
        if token:
            request.user.fcm_token = token
            request.user.save(update_fields=['fcm_token'])
            return JsonResponse({"status": "saved"})
        return JsonResponse({"status": "error", "message": "token missing"}, status=400)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


@login_required
def poll_active_alerts(request):
    """
    Real-time polling endpoint for in-app alert sirens, popups, and navbar badge.
    Checks:
    1. Total unread notifications count
    2. Active SOS emergency distress broadcasts within 3 km of user's latest location or where user is notified.
    """
    unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    
    from emergency.models import Emergency
    from tracking.models import Location
    from local_residents.models import LocalResident

    latest_loc = Location.objects.filter(user=request.user).order_by('-timestamp').first()
    res = LocalResident.objects.filter(user=request.user).first()
    user_lat = (res.latitude if res and res.latitude else None) or (latest_loc.latitude if latest_loc else getattr(request.user, 'latitude', None))
    user_lng = (res.longitude if res and res.longitude else None) or (latest_loc.longitude if latest_loc else getattr(request.user, 'longitude', None))

    active_alert = None
    active_emergencies = Emergency.objects.filter(status='ACTIVE').exclude(victim=request.user).order_by('-created_at')

    for em in active_emergencies:
        is_notified = em.resident_responses.filter(resident__user=request.user).exists() or em.notified_contacts.filter(id=request.user.id).exists()
        dist = None
        if user_lat is not None and user_lng is not None and em.latitude is not None and em.longitude is not None:
            dist = em._haversine_distance(float(user_lat), float(user_lng), float(em.latitude), float(em.longitude))

        if is_notified or (dist is not None and dist <= 3.0):
            dist_text = f"{int(dist * 1000)} m" if (dist is not None and dist < 1) else (f"{dist:.1f} km" if dist is not None else "Nearby")
            victim_name = em.victim.full_name or em.victim.username
            active_alert = {
                'id': em.id,
                'victim_name': victim_name,
                'victim_phone': getattr(em.victim, 'phone', ''),
                'distance_text': dist_text,
                'distance_km': round(dist, 2) if dist is not None else None,
                'created_at': em.created_at.strftime('%H:%M:%S'),
                'description': em.description or 'Immediate citizen intervention required',
                'track_url': f"/emergency/{em.id}/track/",
                'accept_url': f"/emergency/{em.id}/accept/",
            }
            break

    return JsonResponse({
        'unread_count': unread_count,
        'active_alert': active_alert,
    })