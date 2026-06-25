from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Guardian
from .forms import GuardianRegistrationForm


@login_required
def guardian_register(request):
    try:
        guardian = Guardian.objects.get(user=request.user)
        return redirect('guardian_profile')
    except Guardian.DoesNotExist:
        pass

    form = GuardianRegistrationForm()
    if request.method == 'POST':
        form = GuardianRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            guardian = form.save(commit=False)
            guardian.user = request.user
            guardian.save()
            request.user.role = 'guardian'
            request.user.save()
            messages.success(request, 'Guardian registration submitted! Awaiting verification.')
            return redirect('guardian_profile')

    return render(request, 'guardians/register.html', {'form': form})


@login_required
def guardian_profile(request):
    guardian = get_object_or_404(Guardian, user=request.user)
    return render(request, 'guardians/profile.html', {'guardian': guardian})


@login_required
def toggle_availability(request):
    guardian = get_object_or_404(Guardian, user=request.user, is_verified=True)
    guardian.is_available = not guardian.is_available
    guardian.save()
    status = 'available' if guardian.is_available else 'unavailable'
    messages.success(request, f'You are now {status}.')
    return redirect('guardian_profile')


@login_required
def update_location(request):
    if request.method == 'POST':
        guardian = get_object_or_404(Guardian, user=request.user)
        guardian.latitude = request.POST.get('latitude')
        guardian.longitude = request.POST.get('longitude')
        guardian.save()
        return redirect('guardian_profile')
    return redirect('guardian_profile')


def guardian_list(request):
    guardians = Guardian.objects.filter(is_verified=True).select_related('user')
    return render(request, 'guardians/list.html', {'guardians': guardians})
