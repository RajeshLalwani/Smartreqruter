import os
import sys
import django
import traceback

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '2_AI_Modules'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartrecruit_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from jobs.models import JobPosting, Application
from django.test import RequestFactory
from jobs.views import ai_hr_interview, ai_interview, take_assessment
from django.contrib.messages.storage.fallback import FallbackStorage

User = get_user_model()
factory = RequestFactory()

# Use our existing test user
user = User.objects.get(username='test_applicant2')
job = JobPosting.objects.get(title='Test Job 2')
app = Application.objects.get(job=job, candidate__user=user)

def run_round(view_func, url, post_data=None, required_status=None):
    if required_status:
        app.status = required_status
        app.save()
        
    print(f"\\n--- Testing {view_func.__name__} (Initial Status: {app.status}) ---")
    
    if post_data:
        request = factory.post(url, post_data)
    else:
        request = factory.get(url)
        
    request.user = user
    setattr(request, 'session', {})
    messages = FallbackStorage(request)
    setattr(request, '_messages', messages)

    try:
        response = view_func(request, app.id) if view_func != take_assessment else view_func(request, app.id, 'aptitude')
        print(f"Response status: {response.status_code}")
        for message in messages:
            print(f"MESSAGE: {message}")
            
        app.refresh_from_db()
        print(f"New Application Status: {app.status}")
    except Exception as e:
        print(f"Error testing {view_func.__name__}: {e}")
        traceback.print_exc()

# Test 1: Aptitude Test (GET)
run_round(take_assessment, f'/jobs/assessment/{app.id}/aptitude/', required_status='RESUME_SELECTED')

# Test 2: AI Interview (POST - Submit Answer)
# Note: In the actual flow, Round 1 Passed -> Round 2 Pending -> Round 2 Passed -> Round 3 Pending
# We skip to ROUND_2_PASSED to test the AI Interview logic
run_round(ai_interview, f'/jobs/interview/ai/{app.id}/', post_data={'answer': 'I am very good at Python.'}, required_status='ROUND_2_PASSED')

# Test 3: HR Interview (POST - Submit Answer)
# HR interview requires ROUND_3_PASSED or HR_ROUND_PENDING
run_round(ai_hr_interview, f'/jobs/interview/hr/{app.id}/', post_data={'answer': 'My greatest strength is learning quickly.'}, required_status='ROUND_3_PASSED')
