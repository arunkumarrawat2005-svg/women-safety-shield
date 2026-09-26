from django.contrib import admin
from django.utils import timezone
from .models import VerificationRequest


@admin.register(VerificationRequest)
class VerificationRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'aadhaar_document_ref', 'reviewed_by', 'created_at', 'reviewed_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'user__email', 'aadhaar_document_ref')
    actions = ['approve_requests', 'reject_requests']

    def approve_requests(self, request, queryset):
        for req in queryset:
            req.status = 'approved'
            req.reviewed_by = request.user
            req.reviewed_at = timezone.now()
            req.save()
            req.user.is_verified = True
            req.user.save()
            if hasattr(req.user, 'local_resident_profile'):
                lr = req.user.local_resident_profile
                lr.is_verified = True
                lr.verified_by = request.user
                lr.verified_at = timezone.now()
                lr.save()
        self.message_user(request, f'{queryset.count()} requests approved.')

    def reject_requests(self, request, queryset):
        queryset.update(status='rejected', reviewed_by=request.user, reviewed_at=timezone.now())
        self.message_user(request, f'{queryset.count()} requests rejected.')
