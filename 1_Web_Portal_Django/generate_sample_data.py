import os
import sys
import django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from django.utils import timezone
from datetime import timedelta
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartrecruit_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from jobs.models import JobPosting, Candidate, Application

User = get_user_model()
recruiter = User.objects.filter(is_superuser=True).first()

if not recruiter:
    recruiter = User.objects.first()
    
if recruiter:
    candidates = []
    for i in range(1, 21):
        # Create users safely
        try:
            user, created = User.objects.get_or_create(
                username=f'samplecand{i}', 
                defaults={'email': f'cand{i}@example.com'}
            )
            if created:
                user.set_password('pass123')
                if hasattr(user, 'is_candidate'): 
                    user.is_candidate = True
                user.save()
            
            c, created = Candidate.objects.get_or_create(
                user=user, 
                defaults={
                    'full_name': f'Sample Candidate {i}',
                    'email': user.email,
                    'experience_years': random.randint(1, 8),
                    'skills_extracted': random.choice(['Python, Django', 'React, JS', 'Java, Spring', 'Node.js, Express'])
                }
            )
            candidates.append(c)
        except Exception as e:
            print(f"Error creating candidate {i}: {e}")

    # Add a specific job matching the screenshot if it doesn't exist
    jobs = []
    for t in ['Senior AI Engineer', 'Python Developer', 'php']:
        j, created = JobPosting.objects.get_or_create(
            title=t, 
            recruiter=recruiter, 
            defaults={
                'location': 'V.V. Nagar' if t == 'Senior AI Engineer' else 'Anand' if t == 'Python Developer' else 'none',
                'status': 'OPEN'
            }
        )
        jobs.append(j)
        
    for j in jobs:
        for c in random.sample(candidates, random.randint(8, 15)):
            try:
                app, created = Application.objects.get_or_create(
                    job=j, 
                    candidate=c, 
                    defaults={
                        'status': random.choice(['APPLIED', 'RESUME_SCREENING', 'ROUND_1_PASSED', 'ROUND_2_PASSED', 'ROUND_3_PASSED', 'OFFER_ACCEPTED', 'REJECTED'])
                    }
                )
                if created:
                    Application.objects.filter(id=app.id).update(
                        applied_at=timezone.now() - timedelta(days=random.randint(1, 30))
                    )
            except Exception as e:
                pass
    print("Sample data populated!")
else:
    print("No recruiter/admin user found to attach jobs to.")
