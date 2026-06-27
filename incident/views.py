from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import IncidentEvent, IncidentReport
from emergency.models import Emergency


@login_required
def incident_timeline(request, emergency_id):
    emergency = get_object_or_404(Emergency, pk=emergency_id)
    events = IncidentEvent.objects.filter(emergency=emergency).order_by('timestamp')
    return render(request, 'incident/timeline.html', {'emergency': emergency, 'events': events})


@login_required
def incident_report(request, emergency_id):
    emergency = get_object_or_404(Emergency, pk=emergency_id)
    events = IncidentEvent.objects.filter(emergency=emergency).order_by('timestamp')
    from tracking.models import Location
    locations = Location.objects.filter(emergency=emergency).order_by('timestamp')

    try:
        report = IncidentReport.objects.get(emergency=emergency)
    except IncidentReport.DoesNotExist:
        report = None

    return render(request, 'incident/report.html', {
        'emergency': emergency,
        'events': events,
        'locations': locations,
        'report': report,
    })


@login_required
def incident_list(request):
    if request.user.role in ['admin', 'organization']:
        emergencies = Emergency.objects.filter(status='CLOSED').order_by('-created_at')
    else:
        emergencies = Emergency.objects.filter(victim=request.user, status='CLOSED').order_by('-created_at')
    return render(request, 'incident/list.html', {'emergencies': emergencies})
