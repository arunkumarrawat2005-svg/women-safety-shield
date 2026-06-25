from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import SafetyZone, SafetyReport
from .serializers import SafetyZoneSerializer, SafetyReportSerializer


class SafetyMapAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        zones = SafetyZone.objects.all()
        reports = SafetyReport.objects.order_by('-created_at')[:50]
        return Response({
            'zones': SafetyZoneSerializer(zones, many=True).data,
            'reports': SafetyReportSerializer(reports, many=True).data,
        })


class SubmitSafetyReportAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SafetyReportSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response({'success': True, 'report': serializer.data}, status=201)
        return Response({'success': False, 'errors': serializer.errors}, status=400)
