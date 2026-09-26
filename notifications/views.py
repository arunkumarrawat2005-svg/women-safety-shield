from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Notification
import json



@login_required
def notification_list(request):
    notifications = Notification.objects.filter(recipient=request.user)[:30]
    return render(request, 'notifications/list.html', {'notifications': notifications})

@login_required
def mark_read(request, pk):
    Notification.objects.filter(pk=pk, recipient=request.user).update(is_read=True)
    return JsonResponse({'success': True})

@login_required
def mark_all_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'success': True})


from django.http import JsonResponse as JR
from django.contrib.auth.decorators import login_required as lr

@lr
def notification_count(request):
    from .models import Notification
    count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return JR({'count': count})

@login_required
def save_token(request):
    try:
        data = json.loads(request.body.decode('utf-8') or '{}')
        token = data.get("token")
        if token:
            request.user.fcm_token = token
            request.user.save(update_fields=['fcm_token'])
            return JsonResponse({"status": "saved"})
        return JsonResponse({"status": "error", "message": "token missing"}, status=400)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)