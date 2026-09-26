from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import VerificationRequest
from .serializers import VerificationRequestSerializer


class SubmitVerificationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        req, created = VerificationRequest.objects.get_or_create(user=request.user)
        ref = request.data.get('aadhaar_document_ref', '')
        doc = request.FILES.get('additional_documents')

        req.aadhaar_document_ref = ref
        if doc:
            req.additional_documents = doc
        req.status = 'pending'
        req.save()

        return Response({
            'success': True,
            'message': 'Verification submitted for review',
            'verification': VerificationRequestSerializer(req).data
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class VerificationStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        req = VerificationRequest.objects.filter(user=request.user).first()
        if not req:
            return Response({'status': 'unverified', 'message': 'No verification request on file'})
        return Response({
            'success': True,
            'verification': VerificationRequestSerializer(req).data
        })


class ReviewVerificationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        if not request.user.is_staff:
            return Response({'success': False, 'message': 'Staff permission required'}, status=403)

        req = get_object_or_404(VerificationRequest, id=id)
        new_status = request.data.get('status')
        if new_status not in ['approved', 'rejected']:
            return Response({'success': False, 'message': 'Invalid status. Choose approved or rejected.'}, status=400)

        req.status = new_status
        req.reviewed_by = request.user
        req.reviewed_at = timezone.now()
        req.notes = request.data.get('notes', '')
        req.save()

        # Update linked profile
        req.user.is_verified = (new_status == 'approved')
        req.user.save()

        # Update local resident profile if present
        if hasattr(req.user, 'local_resident_profile'):
            profile = req.user.local_resident_profile
            profile.is_verified = (new_status == 'approved')
            profile.verified_by = request.user
            profile.verified_at = timezone.now()
            profile.save()

        return Response({
            'success': True,
            'message': f'Verification request {new_status}.',
            'verification': VerificationRequestSerializer(req).data
        })
