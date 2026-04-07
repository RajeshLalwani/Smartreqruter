from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import RegexValidator

# =========================================================
# CRITICAL FIX: Correct Import Paths
# =========================================================
from .models import User  # 'User' is in the 'core' app
from jobs.models import JobPosting, Candidate  # 'JobPosting' & 'Candidate' are in the 'jobs' app!

# ==========================================
# 1. CUSTOM REGISTRATION FORM (Auth Fix)
# ==========================================
class CustomUserCreationForm(UserCreationForm):
    full_name = forms.CharField(label="Full Name", max_length=150, required=True)

    class Meta:
        model = User  # Uses your custom 'core.User'
        fields = ['username', 'email'] # Fields to save (extra fields are handled manually)
    
    # Auto-apply "Glass Input" styling to any other fields
    def __init__(self, *args, **kwargs):
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            current_classes = field.widget.attrs.get('class', '')
            new_classes = f"{current_classes} form-control glass-input".strip()
            field.widget.attrs.update({
                'class': new_classes,
                'placeholder': field.label or field_name.replace('_', ' ').title()
            })
        
        # Safe access to account_type if it's added dynamically or inherited
        if 'account_type' in self.fields:
            self.fields['account_type'].widget.attrs.update({'class': 'form-select glass-input'})

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.is_candidate = True # Everyone registering publicly is a candidate
        user.is_recruiter = False
            
        full_name = self.cleaned_data.get('full_name', '')
        if full_name:
            # Proper split for first and last names
            name_parts = full_name.strip().split(' ', 1)
            user.first_name = name_parts[0]
            if len(name_parts) > 1:
                user.last_name = name_parts[1]
            else:
                user.last_name = ""
        
        if commit:
            user.save()
        return user

# ==========================================
# 2. JOB POSTING FORM (Preserved)
# ==========================================
class JobPostingForm(forms.ModelForm):
    class Meta:
        model = JobPosting
        fields = ['title', 'job_type', 'technology_stack', 'location', 'salary_range', 'deadline', 'description', 'required_skills', 'min_experience', 'status']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control glass-input', 'placeholder': 'e.g. Senior AI Engineer'}),
            'job_type': forms.Select(attrs={'class': 'form-control glass-input'}),
            'technology_stack': forms.Select(attrs={'class': 'form-control glass-input'}),
            'location': forms.Select(attrs={'class': 'form-control glass-input'}),
            'salary_range': forms.TextInput(attrs={'class': 'form-control glass-input', 'placeholder': 'e.g. 12 LPA - 18 LPA'}),
            'deadline': forms.DateInput(attrs={'class': 'form-control glass-input', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-control glass-input', 'rows': 4, 'placeholder': 'Job details...'}),
            'required_skills': forms.TextInput(attrs={'class': 'form-control glass-input', 'placeholder': 'e.g. Python, SQL'}),
            'min_experience': forms.NumberInput(attrs={'class': 'form-control glass-input'}),
            'status': forms.Select(attrs={'class': 'form-control glass-input'}),
        }

# ==========================================
# 3. CANDIDATE FORM (Preserved)
# ==========================================
class CandidateForm(forms.ModelForm):
    full_name = forms.CharField(
        validators=[RegexValidator(r'^[a-zA-Z\s]*$', 'Only characters are allowed.')],
        widget=forms.TextInput(attrs={'class': 'form-control glass-input', 'placeholder': 'Full Name'})
    )
    phone = forms.CharField(
        validators=[RegexValidator(r'^\d{10}$', 'Phone must be exactly 10 digits.')],
        widget=forms.TextInput(attrs={'class': 'form-control glass-input', 'placeholder': '10-digit Mobile'})
    )

    class Meta:
        model = Candidate
        fields = ['full_name', 'email', 'phone', 'experience_years', 'resume_file']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control glass-input', 'placeholder': 'name@example.com'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control glass-input'}),
            'resume_file': forms.FileInput(attrs={'class': 'form-control glass-input'}),
        }
