from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from emergency.models import Emergency
from guardians.models import Guardian
from safety_map.models import SafetyReport

@login_required
def org_dashboard(request):
    if request.user.role != 'organization':
        messages.error(request, 'Organization access only.')
        return redirect('dashboard')
    context = {
        'active_emergencies': Emergency.objects.filter(status__in=['ACTIVE','ACCEPTED']).count(),
        'total_emergencies': Emergency.objects.count(),
        'verified_guardians': Guardian.objects.filter(is_verified=True).count(),
        'recent_reports': SafetyReport.objects.order_by('-created_at')[:10],
        'recent_emergencies': Emergency.objects.order_by('-created_at')[:10],
    }
    return render(request, 'organization/dashboard.html', context)
