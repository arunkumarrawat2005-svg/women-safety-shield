from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import TrustedContact, SafetyAlert
from accounts.models import User
from notifications.models import Notification
from notifications.services import trigger_twilio_call_or_sms


@login_required
def trusted_contacts(request):
    contacts = TrustedContact.objects.filter(
        user=request.user, is_active=True
    ).select_related('contact').order_by('-is_primary', '-added_at')
    
    contact_count = contacts.count()
    primary_contact = contacts.filter(is_primary=True).first()

    # Calculate Circle Readiness & Strength Score
    if contact_count == 0:
        score = 0
        score_status = "Critical Vulnerability"
        score_badge = "Not Protected"
        score_color = "danger"
        score_advice = "Add at least 1 primary contact immediately so alerts reach someone during SOS."
    elif contact_count == 1:
        score = 40
        score_status = "Basic Coverage"
        score_badge = "Partially Protected"
        score_color = "warning"
        score_advice = "Good start! Add 2 more contacts (family + nearby friend or neighbor) for optimal safety."
    elif contact_count == 2:
        score = 75
        score_status = "Good Coverage"
        score_badge = "Moderate Protection"
        score_color = "info"
        score_advice = "Almost complete! Consider designating a primary guardian and a local responder."
    else:
        score = 100
        score_status = "Maximum Protection"
        score_badge = "Fully Reinforced"
        score_color = "success"
        score_advice = "Your trusted safety shield is fully reinforced across multi-tier emergency channels."

    # Channel stats
    sms_count = contacts.filter(alert_sms=True).count()
    whatsapp_count = contacts.filter(alert_whatsapp=True).count()
    location_count = contacts.filter(can_view_location=True).count()
    tested_count = contacts.filter(last_tested_at__isnull=False).count()

    # Registered users not yet in user's circle
    registered_contact_ids = contacts.filter(contact__isnull=False).values_list('contact_id', flat=True)
    all_users = User.objects.exclude(id=request.user.id).exclude(id__in=registered_contact_ids)

    return render(request, 'community/trusted_contacts.html', {
        'contacts': contacts,
        'contact_count': contact_count,
        'primary_contact': primary_contact,
        'score': score,
        'score_status': score_status,
        'score_badge': score_badge,
        'score_color': score_color,
        'score_advice': score_advice,
        'sms_count': sms_count,
        'whatsapp_count': whatsapp_count,
        'location_count': location_count,
        'tested_count': tested_count,
        'all_users': all_users,
        'relation_choices': TrustedContact.RELATION_CHOICES,
    })


@login_required
def add_trusted_contact(request):
    if request.method == 'POST':
        add_type = request.POST.get('add_type', 'phone')
        relation = request.POST.get('relation', 'other')
        is_primary = request.POST.get('is_primary') in ['1', 'on', 'true']

        if is_primary:
            TrustedContact.objects.filter(user=request.user, is_primary=True).update(is_primary=False)

        if add_type == 'user':
            contact_id = request.POST.get('contact_id')
            try:
                contact_user = User.objects.get(id=contact_id)
                tc, created = TrustedContact.objects.get_or_create(
                    user=request.user, contact=contact_user,
                    defaults={
                        'relation': relation,
                        'is_primary': is_primary,
                        'alert_sms': True,
                        'alert_whatsapp': True,
                        'alert_call': True,
                        'can_view_location': True,
                    }
                )
                if not created:
                    tc.relation = relation
                    tc.is_primary = is_primary
                    tc.is_active = True
                    tc.save()
                messages.success(request, f'✅ {contact_user.full_name} added to your Trusted Circle.')
            except User.DoesNotExist:
                messages.error(request, 'Selected user could not be found.')
        else:
            name = request.POST.get('name', '').strip()
            phone = request.POST.get('phone', '').strip()
            email = request.POST.get('email', '').strip()

            if not name or not phone:
                messages.error(request, 'Contact name and phone number are required.')
                return redirect('trusted_contacts')

            # Auto-link registered user if phone matches
            matched_user = User.objects.filter(phone=phone).exclude(id=request.user.id).first()
            if not matched_user and email:
                matched_user = User.objects.filter(email=email).exclude(id=request.user.id).first()

            tc = TrustedContact.objects.create(
                user=request.user,
                contact=matched_user,
                name=name,
                phone=phone,
                email=email,
                relation=relation,
                is_primary=is_primary,
                alert_sms=True,
                alert_whatsapp=True,
                alert_call=True,
                can_view_location=True,
            )
            linked_badge = " (Linked to platform account)" if matched_user else ""
            messages.success(request, f'✅ {name} added to your Trusted Circle as emergency contact{linked_badge}.')

    return redirect('trusted_contacts')


@login_required
def toggle_primary_contact(request, pk):
    contact = get_object_or_404(TrustedContact, pk=pk, user=request.user)
    if not contact.is_primary:
        TrustedContact.objects.filter(user=request.user, is_primary=True).update(is_primary=False)
        contact.is_primary = True
        messages.success(request, f'⭐ {contact.display_name} is now designated as your Primary Emergency Guardian.')
    else:
        contact.is_primary = False
        messages.info(request, f'{contact.display_name} is no longer designated as primary guardian.')
    contact.save()
    return redirect('trusted_contacts')


@login_required
def test_trusted_contact(request, pk):
    contact = get_object_or_404(TrustedContact, pk=pk, user=request.user)
    contact.last_tested_at = timezone.now()
    contact.save()

    user_name = request.user.full_name or request.user.username

    # In-app notification if registered user
    if contact.contact:
        Notification.objects.create(
            recipient=contact.contact,
            title='🧪 Circle Drill: Test Safety Ping',
            message=f'{user_name} conducted a Women Safety Shield connection drill. All emergency systems nominal.',
            notif_type='info'
        )

    # Simulated SMS/voice dispatch
    phone = contact.display_phone
    if phone:
        trigger_twilio_call_or_sms(
            phone,
            f"[TEST ALERT] Women Safety Shield drill test from {user_name}. Everything is OK. No action required."
        )

    messages.success(request, f'🧪 Safety drill ping sent to {contact.display_name}! Connection verified.')
    return redirect('trusted_contacts')


@login_required
@require_POST
def send_safe_checkin(request):
    custom_msg = request.POST.get('message', '').strip()
    user_name = request.user.full_name or request.user.username
    now_str = timezone.now().strftime("%I:%M %p, %d %b %Y")
    
    body = custom_msg or f"I have reached safely at {now_str}. My status is secure."
    contacts = TrustedContact.objects.filter(user=request.user, is_active=True)

    if not contacts.exists():
        messages.warning(request, 'You have no trusted contacts in your circle to notify.')
        return redirect('trusted_contacts')

    sent_count = 0
    for tc in contacts:
        if tc.contact:
            Notification.objects.create(
                recipient=tc.contact,
                title="✅ I'm Safe Check-in",
                message=f"{user_name}: {body}",
                notif_type='info'
            )
            sent_count += 1
        phone = tc.display_phone
        if phone and tc.alert_sms:
            trigger_twilio_call_or_sms(phone, f"[SAFE CHECK-IN] Women Safety Shield: {user_name} sent a safe arrival check-in: '{body}'")
            if not tc.contact:
                sent_count += 1

    SafetyAlert.objects.create(
        sender=request.user,
        message=f"Safe Check-in broadcast: {body}"
    )

    messages.success(request, f'✅ Safe check-in successfully broadcast to your trusted circle ({contacts.count()} contacts).')
    return redirect('trusted_contacts')


@login_required
def edit_trusted_contact(request, pk):
    contact = get_object_or_404(TrustedContact, pk=pk, user=request.user)
    if request.method == 'POST':
        contact.relation = request.POST.get('relation', contact.relation)
        new_name = request.POST.get('name', '').strip()
        if new_name:
            contact.name = new_name
        if not contact.contact:
            contact.phone = request.POST.get('phone', contact.phone).strip() or contact.phone
            contact.email = request.POST.get('email', contact.email).strip()

        contact.alert_sms = request.POST.get('alert_sms') in ['1', 'on', 'true']
        contact.alert_whatsapp = request.POST.get('alert_whatsapp') in ['1', 'on', 'true']
        contact.alert_call = request.POST.get('alert_call') in ['1', 'on', 'true']
        contact.can_view_location = request.POST.get('can_view_location') in ['1', 'on', 'true']
        contact.save()
        messages.success(request, f'Settings updated for {contact.display_name}.')
    return redirect('trusted_contacts')


@login_required
def remove_trusted_contact(request, pk):
    contact = get_object_or_404(TrustedContact, pk=pk, user=request.user)
    name = contact.display_name
    contact.delete()
    messages.success(request, f'{name} was removed from your Trusted Circle.')
    return redirect('trusted_contacts')
