from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import TrustedContact
from accounts.models import User


@login_required
def trusted_contacts(request):
    contacts = TrustedContact.objects.filter(user=request.user).select_related('contact')
    all_users = User.objects.exclude(id=request.user.id).exclude(
        id__in=contacts.values_list('contact_id', flat=True)
    )
    return render(request, 'community/trusted_contacts.html', {
        'contacts': contacts,
        'all_users': all_users
    })


@login_required
def add_trusted_contact(request):
    if request.method == 'POST':
        contact_id = request.POST.get('contact_id')
        relation = request.POST.get('relation', 'other')
        try:
            contact = User.objects.get(id=contact_id)
            TrustedContact.objects.get_or_create(
                user=request.user, contact=contact,
                defaults={'relation': relation}
            )
            messages.success(request, f'{contact.full_name} added to your trusted circle.')
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
    return redirect('trusted_contacts')


@login_required
def remove_trusted_contact(request, pk):
    contact = get_object_or_404(TrustedContact, pk=pk, user=request.user)
    contact.delete()
    messages.success(request, 'Contact removed from trusted circle.')
    return redirect('trusted_contacts')
