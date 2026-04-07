import os
import sys
import django
import traceback

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '2_AI_Modules'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartrecruit_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from jobs.models import JobPosting, Candidate, Application
from django.test import RequestFactory
from jobs.views import apply_job
from django.contrib.messages.storage.fallback import FallbackStorage

User = get_user_model()

# Create a dummy user and candidate
user, _ = User.objects.get_or_create(username='test_applicant2', email='test2@test.com')
user.set_password('pass123')
user.save()

# Create a simple job
recruiter = User.objects.filter(is_superuser=True).first()
if not recruiter:
    recruiter = User.objects.first()

job, _ = JobPosting.objects.get_or_create(
    title='Test Job 2',
    recruiter=recruiter,
    status='OPEN',
    description='This is a test job.'
)

# Simulate applying
factory = RequestFactory()
resume_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sample_offer_letter.pdf')
with open(resume_path, 'rb') as f:
    resume = SimpleUploadedFile("resume.pdf", f.read(), content_type="application/pdf")

request = factory.post(f'/jobs/{job.id}/apply/', {'resume': resume})
request.user = user
setattr(request, 'session', {})
messages = FallbackStorage(request)
setattr(request, '_messages', messages)

try:
    response = apply_job(request, job.id)
    print(f"Response status: {response.status_code}")
    for message in messages:
        print(f"MESSAGE: {message}")
except Exception as e:
    traceback.print_exc()

# Let's check if the application was actually saved
app = Application.objects.filter(job=job, candidate__user=user).first()
if app:
    print(f"Application created successfully. ID: {app.id}, Status: {app.status}")
else:
    print("Application was NOT created.")
