from django.contrib import admin
from .models import Organization
@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name','org_type','user','is_verified','created_at')
    list_filter = ('org_type','is_verified')
