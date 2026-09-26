from django import forms
from django.contrib.auth import get_user_model
from .models import Organization

User = get_user_model()


class OrganizationRegistrationForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=False, help_text="Required if you don't have an existing account.")
    first_name = forms.CharField(max_length=50, required=False, label="Contact Officer First Name")
    last_name = forms.CharField(max_length=50, required=False, label="Contact Officer Last Name")
    password = forms.CharField(widget=forms.PasswordInput, required=False)
    password_confirm = forms.CharField(widget=forms.PasswordInput, required=False, label="Confirm Password")

    class Meta:
        model = Organization
        fields = [
            'name', 'org_type', 'address', 'city', 'state',
            'latitude', 'longitude', 'contact_email', 'contact_phone',
            'emergency_helpline', 'operating_hours', 'has_safe_haven',
            'cctv_monitored', 'security_guards_count', 'description'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Describe campus safety protocols, security booths, CCTV coverage, or women safe haven rooms...'}),
            'address': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Campus / Facility address, Street, Sector...'}),
            'latitude': forms.NumberInput(attrs={'step': 'any', 'placeholder': 'e.g. 28.6139'}),
            'longitude': forms.NumberInput(attrs={'step': 'any', 'placeholder': 'e.g. 77.2090'}),
            'emergency_helpline': forms.TextInput(attrs={'placeholder': 'e.g. 011-23456789 or +91 9876543210'}),
            'operating_hours': forms.TextInput(attrs={'placeholder': 'e.g. 24/7 Security Coverage, or 7:00 AM - 11:00 PM'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'

        if not self.user or not self.user.is_authenticated:
            self.fields['username'].required = True
            self.fields['first_name'].required = True
            self.fields['last_name'].required = True
            self.fields['password'].required = True
            self.fields['password_confirm'].required = True

    def clean(self):
        cleaned_data = super().clean()
        if not self.user or not self.user.is_authenticated:
            pw = cleaned_data.get('password')
            pw_conf = cleaned_data.get('password_confirm')
            username = cleaned_data.get('username')

            if pw and pw_conf and pw != pw_conf:
                self.add_error('password_confirm', 'Passwords do not match.')

            if username and User.objects.filter(username=username).exists():
                self.add_error('username', 'This username is already taken.')

            contact_email = cleaned_data.get('contact_email')
            if contact_email and User.objects.filter(email=contact_email).exists():
                self.add_error('contact_email', 'An account with this email already exists. Please log in first.')

        return cleaned_data


class OrganizationProfileEditForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = [
            'name', 'org_type', 'address', 'city', 'state',
            'latitude', 'longitude', 'contact_email', 'contact_phone',
            'emergency_helpline', 'operating_hours', 'has_safe_haven',
            'cctv_monitored', 'security_guards_count', 'description'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'address': forms.Textarea(attrs={'rows': 2}),
            'latitude': forms.NumberInput(attrs={'step': 'any'}),
            'longitude': forms.NumberInput(attrs={'step': 'any'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'


class OrgVolunteerAddForm(forms.Form):
    username = forms.CharField(max_length=150, help_text="Registered user's username or phone")
    role_at_org = forms.ChoiceField(
        choices=[
            ('security_guard', 'Campus Security Guard'),
            ('security_officer', 'Chief Security Officer'),
            ('staff_responder', 'Staff Safety Warden'),
            ('student_volunteer', 'Student Safety Volunteer'),
            ('resident_assistant', 'Hostel / Resident Assistant'),
            ('designated_responder', 'Designated First Responder'),
        ],
        initial='security_guard'
    )
    is_available = forms.BooleanField(required=False, initial=True, label="On-Duty Immediately")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'


class JoinOrganizationForm(forms.Form):
    role_at_org = forms.ChoiceField(
        choices=[
            ('student_volunteer', 'Student Safety Volunteer'),
            ('staff_responder', 'Faculty / Staff Warden'),
            ('security_guard', 'Security Personnel'),
            ('resident_assistant', 'Hostel / Resident Assistant'),
            ('designated_responder', 'Volunteer First Responder'),
        ],
        label="Your Role / Affiliation"
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'e.g. Employee ID, Student Enrollment number, or Shift details...'}),
        required=False,
        label="Affiliation Details (Optional)"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
