from .models import TrustedContact


def get_trusted_contacts(user):
    return TrustedContact.objects.filter(user=user, is_active=True).select_related('contact')
