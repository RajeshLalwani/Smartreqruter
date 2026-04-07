from django import forms
from .models import JobPosting, Question

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'category', 'difficulty', 'options', 'correct_answer']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control glass-input', 'rows': 3}),
            'category': forms.Select(attrs={'class': 'form-select glass-input'}),
            'difficulty': forms.Select(attrs={'class': 'form-select glass-input'}),
            'options': forms.Textarea(attrs={'class': 'form-control glass-input', 'rows': 3, 'placeholder': 'JSON list of options ["A", "B"]'}),
            'correct_answer': forms.TextInput(attrs={'class': 'form-control glass-input'}),
        }

class JobPostingForm(forms.ModelForm):
    class Meta:
        model = JobPosting
        fields = ['title', 'job_type', 'technology_stack', 'location', 'salary_range', 'deadline', 'description', 'required_skills', 'min_experience', 'passing_score_r1', 'passing_score_r2', 'aptitude_difficulty', 'practical_difficulty']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control glass-input', 'placeholder': 'e.g. Senior Python Developer'}),
            'job_type': forms.Select(attrs={'class': 'form-select glass-input'}),
            'technology_stack': forms.Select(attrs={'class': 'form-select glass-input'}),
            'location': forms.TextInput(attrs={'class': 'form-control glass-input', 'placeholder': 'e.g. Remote, New York'}),
            'salary_range': forms.TextInput(attrs={'class': 'form-control glass-input', 'placeholder': 'e.g. $80k - $120k'}),
            'deadline': forms.DateInput(attrs={'class': 'form-control glass-input', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-control glass-input', 'rows': 5, 'placeholder': 'Detailed job description...'}),
            'required_skills': forms.Textarea(attrs={'class': 'form-control glass-input', 'rows': 3, 'placeholder': 'Comma-separated skills (e.g. Python, Django, AWS)'}),
            'min_experience': forms.NumberInput(attrs={'class': 'form-control glass-input', 'min': '0'}),
            'passing_score_r1': forms.TextInput(attrs={'class': 'form-control glass-input', 'type': 'number', 'min': '0', 'max': '100', 'placeholder': '0-100'}),
            'passing_score_r2': forms.TextInput(attrs={'class': 'form-control glass-input', 'type': 'number', 'min': '0', 'max': '100', 'placeholder': '0-100'}),
            'aptitude_difficulty': forms.Select(attrs={'class': 'form-select glass-input'}),
            'practical_difficulty': forms.Select(attrs={'class': 'form-select glass-input'}),
        }
