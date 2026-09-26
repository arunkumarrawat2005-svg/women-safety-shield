from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import SafetyReport


@login_required
def safety_map_view(request):
    """Redirects legacy safety map view to unified Safe Routes & Community Map."""
    return redirect('safe_routes_compare')


@login_required
def submit_report(request):
    """Handles submission of community incident/hazard reports."""
    if request.method == 'POST':
        lat = request.POST.get('latitude')
        lng = request.POST.get('longitude')
        category = request.POST.get('category')
        loc_name = request.POST.get('location_name', '').strip()
        desc = request.POST.get('description', '').strip()
        anon = request.POST.get('is_anonymous') == 'on'

        if lat and lng and category:
            SafetyReport.objects.create(
                user=request.user,
                latitude=float(lat),
                longitude=float(lng),
                location_name=loc_name,
                category=category,
                description=desc,
                is_anonymous=anon,
            )
            messages.success(request, 'Safety hazard report submitted! It is now visible on the Community Safe Map.')
        else:
            messages.error(request, 'Please provide category and location for the safety report.')
    return redirect('safe_routes_compare')
