import os
import django
from django.test import Client
from django.urls import reverse
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartrecruit_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from jobs.models import JobPosting, Application, Question, Interview

User = get_user_model()

def test_all_pages():
    client = Client()
    
    # Get a recruiter user (assuming one exists)
    candidate = User.objects.filter(is_candidate=True).first()
    if not candidate:
        print("No candidate user found. Creating a temporary one.")
        candidate = User.objects.create_user(username='test_candidate', password='password123', is_candidate=True, email='test_cand@example.com')
        from jobs.models import Candidate
        Candidate.objects.create(user=candidate, full_name='Test Cand', email='test_cand@example.com')
    
    client.force_login(candidate)
    
    # Collect sample objects
    job = JobPosting.objects.first()
    application = Application.objects.filter(candidate__user=candidate).first()
    if not application and job:
        try:
            cand_profile = candidate.candidate_profile
        except Exception:
            from jobs.models import Candidate
            cand_profile = Candidate.objects.create(user=candidate, full_name='Test Cand', email=candidate.email)
        application = Application.objects.create(job=job, candidate=cand_profile)

    question = Question.objects.first()
    interview = Interview.objects.first()
    
    endpoints = [
        # core urls
        ('home', {}),
        ('dashboard', {}),
        ('settings', {}),
        
        # jobs urls
        ('job_list', {}),
        
        # candidate urls
        ('candidate_profile', {}),
        ('candidate_applications', {}),
        ('take_mock_test', {})
    ]
    
    if job:
        endpoints.extend([
            ('job_detail', {'job_id': job.id}),
        ])
    
    if application:
        endpoints.extend([
            ('application_details', {'application_id': application.id}),
            ('ai_interview', {'application_id': application.id}),
            ('ai_hr_interview', {'application_id': application.id}),
            ('view_offer', {'application_id': application.id}),
            ('schedule_interview_view', {'application_id': application.id}),
            ('take_assessment', {'application_id': application.id, 'test_type': 'aptitude'})
        ])
        
    if question:
        endpoints.extend([
            ('edit_question', {'question_id': question.id}),
        ])
        
    errors = []
    
    for url_name, kwargs in endpoints:
        try:
            url = reverse(url_name, kwargs=kwargs)
            # Some URLs might require specific methods or fail gracefully. For simplicity, we just do a GET.
            response = client.get(url)
            print(f"[{response.status_code}] {url_name} ({url})")
            if response.status_code >= 500:
                print(f"  --> ERROR: {response.content[:500]}")
                errors.append(f"{url_name} returned {response.status_code}")
        except Exception as e:
            print(f"[EXCEPTION] {url_name} with args {kwargs}: {e}")
            errors.append(f"{url_name} exception: {e}")
            
    if errors:
        print("\n=== ERRORS FOUND ===")
        for e in errors:
            print(e)
    else:
        print("\n=== ALL GOOD! ===")

if __name__ == '__main__':
    test_all_pages()
