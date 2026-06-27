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

    data=json.loads(request.body)

    request.user.fcm_token=data["token"]

    request.user.save()


    return JsonResponse({
        "status":"saved"
    })