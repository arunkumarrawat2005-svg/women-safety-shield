from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Emergency
from .services import EmergencyService


@login_required
def sos_view(request):
    """Main SOS trigger page."""
    active = Emergency.objects.filter(victim=request.user, status='ACTIVE').first()
    context = {
        'active_emergency': active,
    }
    return render(request, 'emergency/sos.html', context)


@login_required
def trigger_sos(request):
    """Handle SOS button press."""
    if request.method == 'POST':
        lat = request.POST.get('latitude')
        lng = request.POST.get('longitude')
        trigger_type = request.POST.get('trigger_type', 'button')

        if not lat or not lng:
            messages.error(request, 'Location is required for SOS.')
            return redirect('sos')

        emergency = EmergencyService.create_emergency(
            user=request.user,
            latitude=float(lat),
            longitude=float(lng),
            trigger_type=trigger_type,
            description=request.POST.get('description', '')
        )
        messages.success(request, f'SOS Alert sent! Emergency #{emergency.id} is active.')
        return redirect('emergency_track', pk=emergency.id)

    return redirect('sos')


@login_required
def emergency_track(request, pk):
    """Live tracking page for an emergency."""
    emergency = get_object_or_404(Emergency, pk=pk)
    if emergency.victim != request.user and request.user not in emergency.notified_contacts.all():
        if not request.user.role in ['admin', 'guardian']:
            messages.error(request, 'Access denied.')
            return redirect('dashboard')

    from incident.models import IncidentEvent
    events = IncidentEvent.objects.filter(emergency=emergency).order_by('timestamp')

    context = {
        'emergency': emergency,
        'events': events,
    }
    return render(request, 'emergency/track.html', context)


@login_required
def emergency_list(request):
    """List of user's emergencies."""
    emergencies = Emergency.objects.filter(victim=request.user).order_by('-created_at')
    return render(request, 'emergency/list.html', {'emergencies': emergencies})


@login_required
def close_emergency(request, pk):
    emergency = get_object_or_404(Emergency, pk=pk, victim=request.user)
    EmergencyService.close_emergency(emergency)
    messages.success(request, 'Emergency closed.')
    return redirect('emergency_list')


@login_required
def guardian_emergencies(request):
    """Guardians view nearby/assigned emergencies."""
    from guardians.models import Guardian
    try:
        guardian = Guardian.objects.get(user=request.user, is_verified=True)
    except Guardian.DoesNotExist:
        messages.error(request, 'You are not a verified guardian.')
        return redirect('dashboard')

    active = Emergency.objects.filter(status__in=['ACTIVE', 'ACCEPTED']).order_by('-created_at')
    return render(request, 'emergency/guardian_view.html', {'emergencies': active, 'guardian': guardian})


@login_required
def accept_emergency(request, pk):
    emergency = get_object_or_404(Emergency, pk=pk)
    EmergencyService.accept_emergency(emergency, request.user)
    messages.success(request, 'You have accepted this emergency. Please proceed to the location.')
    return redirect('emergency_track', pk=pk)
