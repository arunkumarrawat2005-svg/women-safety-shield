from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import User
from emergency.models import Emergency
from guardians.models import Guardian
from safety_map.models import SafetyReport
from django.utils import timezone


@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        messages.error(request, 'Admin access required.')
        return redirect('dashboard')
    context = {
        'total_users': User.objects.count(),
        'total_emergencies': Emergency.objects.count(),
        'active_emergencies': Emergency.objects.filter(status='ACTIVE').count(),
        'total_guardians': Guardian.objects.count(),
        'verified_guardians': Guardian.objects.filter(is_verified=True).count(),
        'pending_guardians': Guardian.objects.filter(is_verified=False).count(),
        'total_reports': SafetyReport.objects.count(),
        'recent_emergencies': Emergency.objects.order_by('-created_at')[:10],
        'pending_guardian_list': Guardian.objects.filter(is_verified=False).select_related('user')[:10],
    }
    return render(request, 'admin_panel/dashboard.html', context)


@login_required
def verify_guardian(request, guardian_id):
    if not request.user.is_staff:
        return redirect('dashboard')
    guardian = get_object_or_404(Guardian, pk=guardian_id)
    guardian.is_verified = True
    guardian.verified_at = timezone.now()
    guardian.verified_by = request.user
    guardian.save()
    messages.success(request, f'{guardian.user.username} has been verified as a guardian.')
    return redirect('admin_dashboard')


@login_required
def user_management(request):
    if not request.user.is_staff:
        return redirect('dashboard')
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'admin_panel/users.html', {'users': users})
