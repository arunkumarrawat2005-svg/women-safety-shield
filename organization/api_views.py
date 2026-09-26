from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Organization, OrgVolunteer, OrgResponse
from .serializers import OrganizationSerializer, OrgVolunteerSerializer, OrgResponseSerializer


class RegisterOrganizationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if hasattr(request.user, 'organization'):
            return Response({'success': False, 'message': 'User already has an organization registered'}, status=400)

        serializer = OrganizationSerializer(data=request.data)
        if serializer.is_valid():
            org = serializer.save(user=request.user)
            request.user.role = 'organization'
            request.user.save()
            return Response({'success': True, 'organization': OrganizationSerializer(org).data}, status=status.HTTP_201_CREATED)
        return Response({'success': False, 'errors': serializer.errors}, status=400)


class AddOrgVolunteerAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, org_id):
        org = get_object_or_404(Organization, id=org_id)
        if org.user != request.user and not request.user.is_staff:
            return Response({'success': False, 'message': 'Only organization owner can add volunteers'}, status=403)

        from accounts.models import User
        user_id = request.data.get('user_id')
        role_at_org = request.data.get('role_at_org', 'designated_responder')

        if not user_id:
            return Response({'success': False, 'message': 'user_id is required'}, status=400)

        volunteer_user = get_object_or_404(User, id=user_id)
        volunteer, created = OrgVolunteer.objects.get_or_create(
            organization=org,
            user=volunteer_user,
            defaults={'role_at_org': role_at_org, 'approved_by_org': True}
        )
        if not created:
            volunteer.role_at_org = role_at_org
            volunteer.approved_by_org = True
            volunteer.save()

        return Response({
            'success': True,
            'volunteer': OrgVolunteerSerializer(volunteer).data
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class AcknowledgeOrgResponseAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, sos_id):
        from emergency.models import Emergency
        from emergency.services import EmergencyService

        try:
            volunteer = OrgVolunteer.objects.get(user=request.user, approved_by_org=True)
        except OrgVolunteer.DoesNotExist:
            return Response({'success': False, 'message': 'User is not an approved organization volunteer'}, status=403)

        try:
            emergency = Emergency.objects.get(pk=sos_id, status='ACTIVE')
        except Emergency.DoesNotExist:
            return Response({'success': False, 'message': 'Active emergency not found'}, status=404)

        resp, _ = OrgResponse.objects.get_or_create(
            sos_event=emergency,
            organization=volunteer.organization,
            defaults={'volunteer': volunteer}
        )
        resp.volunteer = volunteer
        resp.status = 'acknowledged'
        resp.acknowledged_at = timezone.now()
        resp.save()

        EmergencyService.accept_emergency(emergency, request.user)

        return Response({
            'success': True,
            'message': 'Organization response acknowledged.',
            'response': OrgResponseSerializer(resp).data
        })


class OrgDashboardAlertsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, org_id):
        org = get_object_or_404(Organization, id=org_id)
        if org.user != request.user and not request.user.is_staff:
            return Response({'success': False, 'message': 'Forbidden'}, status=403)

        alerts = OrgResponse.objects.filter(organization=org).select_related('sos_event', 'volunteer').order_by('-notified_at')[:50]
        return Response({
            'success': True,
            'alerts': OrgResponseSerializer(alerts, many=True).data
        })
