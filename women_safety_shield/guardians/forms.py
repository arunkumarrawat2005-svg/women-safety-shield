from django import forms
from .models import Guardian


class GuardianRegistrationForm(forms.ModelForm):
    class Meta:
        model = Guardian
        fields = ('guardian_type', 'organization_name', 'description', 'verification_document')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
