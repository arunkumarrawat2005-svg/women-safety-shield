from django import forms
from .models import LocalResident


class LocalResidentRegistrationForm(forms.ModelForm):
    class Meta:
        model = LocalResident
        fields = ('local_resident_type', 'organization_name', 'description', 'verification_document')
        widgets = {
            'local_resident_type': forms.Select(attrs={'class': 'form-select'}),
            'organization_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Brief description'}),
            'verification_document': forms.FileInput(attrs={'class': 'form-control'}),
        }


# Backwards compatibility alias
GuardianRegistrationForm = LocalResidentRegistrationForm
