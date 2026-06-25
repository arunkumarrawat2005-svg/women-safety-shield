from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import TrustedContact
from .serializers import TrustedContactSerializer


class TrustedContactListAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TrustedContactSerializer

    def get_queryset(self):
        return TrustedContact.objects.filter(user=self.request.user)


class AddTrustedContactAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from accounts.models import User
        contact_id = request.data.get('contact_id')
        relation = request.data.get('relation', 'other')
        try:
            contact = User.objects.get(id=contact_id)
            tc, created = TrustedContact.objects.get_or_create(
                user=request.user, contact=contact,
                defaults={'relation': relation}
            )
            return Response({
                'success': True,
                'created': created,
                'contact': TrustedContactSerializer(tc).data
            }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'success': False, 'message': 'User not found'}, status=404)
