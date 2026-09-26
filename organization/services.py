from django.utils import timezone
from django.db.models import Q
from .models import Organization


class OrganizationService:
    @staticmethod
    def get_verified_organizations(category=None, query=None, city=None):
        """Fetch verified organizations with optional filtering."""
        qs = Organization.objects.filter(is_verified=True).select_related('user')
        if category and category != 'all':
            qs = qs.filter(org_type=category)
        if city:
            qs = qs.filter(city__icontains=city)
        if query:
            qs = qs.filter(
                Q(name__icontains=query) |
                Q(address__icontains=query) |
                Q(city__icontains=query) |
                Q(description__icontains=query)
            )
        return qs.order_by('name')

    @staticmethod
    def assign_responder(org_response, volunteer):
        """Assign an approved volunteer to an active SOS event."""
        from emergency.services import EmergencyService

        org_response.volunteer = volunteer
        org_response.status = 'acknowledged'
        org_response.acknowledged_at = timezone.now()
        org_response.save()

        # Update the emergency event
        if org_response.sos_event and org_response.sos_event.status == 'ACTIVE':
            EmergencyService.accept_emergency(org_response.sos_event, volunteer.user)

        return org_response
