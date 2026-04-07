import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# Add AI Modules to path if needed
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '2_AI_Modules'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartrecruit_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from jobs.models import JobPosting, Candidate
from django.test import RequestFactory
from jobs.views import apply_job
from django.contrib.messages.storage.fallback import FallbackStorage

User = get_user_model()

# Create a dummy user and candidate
user, _ = User.objects.get_or_create(username='test_applicant', email='test@test.com')
user.set_password('pass123')
user.save()

# Create a simple job
recruiter = User.objects.filter(is_superuser=True).first()
if not recruiter:
    recruiter = User.objects.first()

job, _ = JobPosting.objects.get_or_create(
    title='Test Job',
    recruiter=recruiter,
    status='OPEN',
    description='This is a test job.'
)

# Simulate applying
factory = RequestFactory()
resume = SimpleUploadedFile("resume.pdf", b"file_content", content_type="application/pdf")

request = factory.post(f'/jobs/{job.id}/apply/', {'resume': resume})
request.user = user
setattr(request, 'session', 'session')
messages = FallbackStorage(request)
setattr(request, '_messages', messages)

try:
    response = apply_job(request, job.id)
    print(f"Response status: {response.status_code}")
except Exception as e:
    import traceback
    traceback.print_exc()
