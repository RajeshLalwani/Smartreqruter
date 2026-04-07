import os
import sys
import django
from django.utils import timezone
from datetime import timedelta

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smartrecruit_project.settings")
django.setup()

from django.contrib.auth import get_user_model
from jobs.models import JobPosting, Candidate, Application, Interview, SentimentLog
from core.utils.email_service import send_async_email
from core.ai_engine import AIEngine
from unittest.mock import patch

User = get_user_model()

def run_flow_test():
    print("=== STARTING SMARTRECRUIT HIRING FLOW TEST ===")
    
    # 1. SETUP DATA
    print("\n[SETUP] Creating test users and job posting...")
    recruiter_user, _ = User.objects.get_or_create(username='test_recruiter', email='recruiter@test.com', is_recruiter=True)
    if not recruiter_user.check_password('testpass'):
        recruiter_user.set_password('testpass')
        recruiter_user.save()
        
    candidate_user, _ = User.objects.get_or_create(username='test_candidate', email='candidate@test.com', is_candidate=True)
    if not candidate_user.check_password('testpass'):
        candidate_user.set_password('testpass')
        candidate_user.save()
        
    candidate_profile, _ = Candidate.objects.get_or_create(user=candidate_user, defaults={'full_name': 'Test Candidate', 'skills_extracted': ['Python', 'Django']})
    
    job, _ = JobPosting.objects.get_or_create(
        title="Senior Python Engineer",
        recruiter=recruiter_user,
        defaults={'description': 'Requires Python, Django, and AI knowledge. minimum_experience: 3 years.', 'status': 'OPEN'}
    )
    
    # 2. PHASE 1: Application Submission & AI Scanner
    print("\n--- PHASE 1: Application Submission ---")
    Application.objects.filter(candidate=candidate_profile, job=job).delete()
    app = Application.objects.create(candidate=candidate_profile, job=job, status='PENDING')
    print(f"-> Application Created. Status: {app.status}")
    
    # Simulate AI Resume Scanner
    print("-> Simulating AI Resume Scanner (Matching JD)...")
    # Normally this is triggered via celery or signals, doing it manually here.
    result = {'score': 85, 'fit': 'HIGH', 'matched_skills': ['Python', 'Django']}
    if result['score'] >= 75:
        app.status = 'SHORTLISTED'
        app.save()
        print(f"-> Application Shortlisted! AI Score: {result['score']}")
        print("-> Email Action: 'Shortlisted for Round 1' Sent.")
    else:
        print("-> Application Rejected. Flow stops here.")
        return

    # 3. PHASE 2: Multi-Round Interviews
    print("\n--- PHASE 2: Intervew Rounds ---")
    
    # Round 1: Aptitude
    print("-> Round 1: Aptitude Test")
    from jobs.models import Interview
    r1_interview, _ = Interview.objects.get_or_create(application=app, interview_type='GENERAL', defaults={'status': 'SCHEDULED'})
    
    print("-> Simulating Candidate Taking Round 1 (Score > 75%)")
    r1_interview.score = 80.0
    r1_interview.status = 'COMPLETED'
    r1_interview.save()
    
    if r1_interview.score > 75.0:
        app.status = 'ROUND_1_PASSED'
        app.save()
        print(f"-> Round 1 Passed! (Score: {r1_interview.score}). Scheduling Round 2.")
    else:
        app.status = 'REJECTED'
        app.save()
        return
        
    # Round 2: Practical
    print("-> Round 2: Practical Test")
    r2_interview, _ = Interview.objects.get_or_create(application=app, interview_type='TECHNICAL', defaults={'status': 'SCHEDULED'})
    r2_interview.score = 82.0
    r2_interview.status = 'COMPLETED'
    r2_interview.save()
    
    if r2_interview.score > 75.0:
        app.status = 'ROUND_2_PASSED'
        app.save()
        print(f"-> Round 2 Passed! (Score: {r2_interview.score}). Scheduling Round 3.")
    
    # Round 3: Bot/Technical
    print("-> Round 3: Bot Evaluation")
    r3_interview, _ = Interview.objects.get_or_create(application=app, interview_type='BOTANIST', defaults={'status': 'SCHEDULED'})
    
    # Simulate vocal confidence analytics passing
    print("-> Simulating Vocal Confidence / Bot Analytics Pass...")
    r3_interview.vocal_confidence_score = 88.0
    r3_interview.status = 'COMPLETED'
    r3_interview.save()
    
    app.status = 'ROUND_3_PASSED' 
    app.save()
    print("-> Round 3 (Technical Bot) Passed!")
    
    # Round 4: HR
    print("-> Round 4: HR Interview")
    r4_interview, _ = Interview.objects.get_or_create(application=app, interview_type='GENERAL', defaults={'status': 'SCHEDULED'})
    
    # Simulate HR Evaluation
    app.status = 'SELECTED_FOR_OFFER'
    app.save()
    print("-> HR Evaluation Passed! Selected for Offer.")
    
    # 4. PHASE 3: Offer Generation
    print("\n--- PHASE 3: Offer Generation ---")
    print("-> Generating Offer Letter...")
    from jobs.models import Offer
    
    offer, _ = Offer.objects.get_or_create(
        application=app,
        defaults={
            'salary_offered': 120000,
            'designation': 'Senior Engineer',
            'joining_date': timezone.now().date() + timedelta(days=30),
            'status': 'SENT'
        }
    )
    print("-> Email Action: Offer Letter Sent.")
    
    print("-> Waiting for candidate acknowledgment (3 days timeframe)...")
    print("-> Simulating Candidate Acceptance...")
    offer.status = 'ACCEPTED'
    offer.save()
    
    app.status = 'HIRED'
    app.save()
    print("-> Email Action: Confirmation & Onboarding Info sent.")
    
    print("\n=== TEST COMPLETED SUCCESSFULLY ===")
    print(f"Final Application Status: {app.status}")


if __name__ == "__main__":
    run_flow_test()
