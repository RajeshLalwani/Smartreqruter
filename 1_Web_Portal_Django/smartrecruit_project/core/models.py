from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    is_candidate = models.BooleanField(default=False)
    is_recruiter = models.BooleanField(default=False)
    
    # Profile fields
    professional_title = models.CharField(max_length=150, blank=True)
    profile_pic = models.ImageField(upload_to='profiles/', blank=True, null=True)
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    
    # AI Score Stats
    resume_score = models.FloatField(default=0.0)
    
    # Settings
    blind_hiring = models.BooleanField(default=False, help_text="Hide candidate names and photos")
    
    VOICE_CHOICES = [
        ('female', 'Aria (Female)'),
        ('male', 'Guy (Male)'),
    ]
    voice_preference = models.CharField(max_length=10, choices=VOICE_CHOICES, default='female')
    
    MODEL_CHOICES = [
        ('gemini-2.0-flash', 'Gemini 1.5 Flash (Fast)'),
        ('gemini-1.5-pro', 'Gemini 1.5 Pro (Deep)'),
    ]
    model_preference = models.CharField(max_length=20, choices=MODEL_CHOICES, default='gemini-2.0-flash')

    def __str__(self):
        return self.username


