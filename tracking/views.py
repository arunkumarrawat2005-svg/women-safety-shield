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
