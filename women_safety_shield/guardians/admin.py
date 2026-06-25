from django.contrib import admin
from .models import Guardian
from django.utils import timezone

@admin.register(Guardian)
class GuardianAdmin(admin.ModelAdmin):
    list_display = ('user', 'guardian_type', 'is_verified', 'is_available', 'trust_score', 'total_responses')
    list_filter = ('is_verified', 'is_available', 'guardian_type')
    search_fields = ('user__username', 'user__email', 'organization_name')
    actions = ['verify_guardians']

    def verify_guardians(self, request, queryset):
        queryset.update(is_verified=True, verified_at=timezone.now(), verified_by=request.user)
        self.message_user(request, f'{queryset.count()} guardians verified.')
    verify_guardians.short_description = 'Verify selected guardians'
