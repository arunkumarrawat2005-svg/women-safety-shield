from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import SafetyZone, SafetyReport


@login_required
def safety_map_view(request):
    zones = SafetyZone.objects.all()
    recent_reports = SafetyReport.objects.order_by('-created_at')[:20]
    return render(request, 'safety_map/map.html', {'zones': zones, 'recent_reports': recent_reports})


@login_required
def submit_report(request):
    if request.method == 'POST':
        SafetyReport.objects.create(
            user=request.user,
            latitude=request.POST.get('latitude'),
            longitude=request.POST.get('longitude'),
            location_name=request.POST.get('location_name', ''),
            category=request.POST.get('category'),
            description=request.POST.get('description', ''),
            is_anonymous=request.POST.get('is_anonymous') == 'on',
        )
        messages.success(request, 'Safety report submitted. Thank you!')
    return redirect('safety_map')
