from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from .models import User
from .forms import RegisterForm, LoginForm, ProfileForm


def home_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'accounts/home.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = RegisterForm()
    if request.method == 'POST':
        form = RegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome {user.full_name}! Your account has been created.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = LoginForm()
    if request.method == 'POST':
        form = LoginForm(request.POST)
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, f'Welcome back, {user.full_name}!')
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out safely.')
    return redirect('home')


@login_required
def dashboard_view(request):
    from emergency.models import Emergency
    from community.models import TrustedContact
    from guardians.models import Guardian

    user = request.user
    active_emergencies = Emergency.objects.filter(victim=user, status='ACTIVE').count()
    trusted_contacts = TrustedContact.objects.filter(user=user).count()
    
    context = {
        'user': user,
        'active_emergencies': active_emergencies,
        'trusted_contacts': trusted_contacts,
    }
    
    if user.role == 'guardian':
        try:
            guardian = Guardian.objects.get(user=user)
            context['guardian'] = guardian
        except Guardian.DoesNotExist:
            context['guardian'] = None
    
    return render(request, 'accounts/dashboard.html', context)


@login_required
def profile_view(request):
    form = ProfileForm(instance=request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    return render(request, 'accounts/profile.html', {'form': form})
