import os
import json
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.http import HttpResponse, JsonResponse, FileResponse
from .models import User
from .forms import RegisterForm, LoginForm, ProfileForm


def home_view(request):
    context = {}
    if request.user.is_authenticated:
        from emergency.models import Emergency
        from community.models import TrustedContact
        from local_residents.models import LocalResident

        user = request.user
        context['active_emergencies'] = Emergency.objects.filter(victim=user, status='ACTIVE').count()
        context['trusted_contacts'] = TrustedContact.objects.filter(user=user).count()
        context['recent_emergencies'] = Emergency.objects.filter(victim=user).order_by('-created_at')[:5]
        context['user_org'] = getattr(user, 'organization', None)

        if user.is_local_resident():
            try:
                context['resident'] = LocalResident.objects.get(user=user)
                context['guardian'] = context['resident']
            except LocalResident.DoesNotExist:
                context['resident'] = None
                context['guardian'] = None

        if user.is_staff:
            context['total_users'] = User.objects.count()
            context['admin_active_emergencies'] = Emergency.objects.filter(status='ACTIVE').count()
            context['verified_residents'] = LocalResident.objects.filter(is_verified=True).count()
            context['pending_residents'] = LocalResident.objects.filter(is_verified=False).count()
            context['pending_resident_list'] = LocalResident.objects.filter(is_verified=False).select_related('user')[:5]
            context['admin_recent_emergencies'] = Emergency.objects.all().order_by('-created_at')[:5]

    return render(request, 'accounts/home.html', context)


def how_it_works_view(request):
    """Interactive Onboarding & Platform Walkthrough ('Understand -> Verify -> Protect')."""
    return render(request, 'accounts/how_it_works.html')


def permission_model_view(request):
    """User Access Levels & Verification-Based Permission Model ('Anyone can seek help, only verified users can provide assistance')."""
    return render(request, 'accounts/permission_model.html')



def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    form = RegisterForm()
    if request.method == 'POST':
        form = RegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(
                request,
                f'Welcome {user.full_name}! Step 1 (Basic Account) created successfully. '
                'Please complete Step 2 (Identity Verification) & Step 3 (Safety Assessment) to activate trusted community features.'
            )
            return redirect('verification_status')
        else:
            messages.error(request, 'Please correct the errors below.')
    return render(request, 'accounts/register.html', {'form': form})



def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    form = LoginForm()
    if request.method == 'POST':
        form = LoginForm(request.POST)
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, f'Welcome back, {user.full_name}!')
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out safely.')
    return redirect('/?logged_out=1')


@login_required
def dashboard_view(request):
    return redirect('home')


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


@login_required
def save_fcm_token(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
        token = data.get("token")

        if not token:
            return JsonResponse({"error": "Token missing"}, status=400)

        request.user.fcm_token = token
        request.user.save(update_fields=['fcm_token'])

        return JsonResponse({
            "message": "Token saved successfully",
            "status": "success"
        })

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def download_apk_view(request):
    apk_candidates = [
        os.path.join(settings.BASE_DIR, 'static', 'downloads', 'women-safety-shield.apk'),
        os.path.join(settings.BASE_DIR, 'android_app', 'WomenSafetyShield.apk'),
    ]
    apk_path = None
    for candidate in apk_candidates:
        if os.path.exists(candidate) and os.path.getsize(candidate) > 5000:
            apk_path = candidate
            break

    if not apk_path or not os.path.exists(apk_path):
        from django.http import Http404
        raise Http404("Official Android APK is currently compiling. Please check back in a moment.")

    response = FileResponse(
        open(apk_path, 'rb'),
        as_attachment=True,
        filename='women-safety-shield.apk',
        content_type='application/vnd.android.package-archive'
    )
    response['Content-Length'] = os.path.getsize(apk_path)
    return response


def manifest_view(request):
    manifest_data = {
        "name": "Women Safety Shield",
        "short_name": "Safety Shield",
        "description": "Community-powered emergency response network with verified residents and automated police dispatch.",
        "start_url": "/",
        "display": "standalone",
        "orientation": "portrait",
        "background_color": "#FDF8F6",
        "theme_color": "#7A1F2B",
        "icons": [
            {
                "src": "/static/images/shield-icon.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any maskable"
            },
            {
                "src": "/static/images/shield-icon.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any maskable"
            }
        ]
    }
    return JsonResponse(manifest_data, content_type='application/manifest+json')


def service_worker_view(request):
    sw_code = """
const CACHE_NAME = 'wss-cache-v2.4';
const OFFLINE_URL = '/';

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(['/']);
        })
    );
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(
                keys.map((key) => {
                    if (key !== CACHE_NAME) return caches.delete(key);
                })
            );
        })
    );
    self.clients.claim();
});

self.addEventListener('fetch', (event) => {
    if (event.request.mode === 'navigate') {
        event.respondWith(
            fetch(event.request).catch(() => caches.match(OFFLINE_URL))
        );
    }
});
"""
    return HttpResponse(sw_code, content_type='application/javascript')


def terms_view(request):
    """Terms of Service, Privacy Policy and Emergency Safety Disclaimer."""
    return render(request, 'accounts/terms.html')

