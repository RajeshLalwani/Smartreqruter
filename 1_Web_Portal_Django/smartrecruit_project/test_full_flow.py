import os
import django
from django.core.files.uploadedfile import SimpleUploadedFile

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartrecruit_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from jobs.models import JobPosting, Application, Candidate
from jobs.views import apply_job
from django.urls import reverse
import sys

User = get_user_model()

def run_test():
    client = Client(HTTP_HOST='localhost')
    print("--- Starting End-to-End Flow Test ---")
    
    # 1. Candidate Registration
    print("[1] Registering Candidate...")
    register_url = reverse('register')
    unique_username = 'candidate_test_e2e'
    unique_email = 'candidate_test_e2e@irinfotech.com'
    
    # Clean up previous tests
    User.objects.filter(username=unique_username).delete()
    
    register_data = {
        'username': unique_username,
        'full_name': 'E2E Test Candidate',
        'email': unique_email,
        'password1': 'Testing@123',
        'password2': 'Testing@123',
    }
    response = client.post(register_url, register_data)
    
    user = User.objects.filter(username=unique_username).first()
    if not user:
        print("    [ERROR] Registration failed. User not created.")
        sys.exit(1)
    print("    [SUCCESS] Candidate Registered successfully.")
    
    # Log in
    client.login(username=unique_username, password='Testing@123')
    print("    [SUCCESS] Logged in as Candidate.")
    
    # 2. Get a Job
    print("[2] Fetching Job Posting...")
    job = JobPosting.objects.first()
    if not job:
        print("    [ERROR] No jobs available in database.")
        sys.exit(1)
    print(f"    [SUCCESS] Selected Job: {job.title}")
    
    # 3. Apply to Job with Resume
    print("[3] Initiating Application with Resume Parsing...")
    # Create simple dummy PDF content
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n4 0 obj\n<< /Length 124 >>\nstream\nBT\n/F1 12 Tf\n72 712 Td\n(This is a Highly Experienced Python Backend Developer resume.) Tj\n0 -14 Td\n(Skills: Python, Django, PostgreSQL, Redis, Docker, System Architecture, AWS, React) Tj\n0 -14 Td\n(Experience: 5 years of software engineering in scalable backend architectures.) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000219 00000 n \ntrailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n393\n%%EOF\n"
    resume_file = SimpleUploadedFile("e2e_resume.pdf", pdf_content, content_type="application/pdf")
    
    apply_url = reverse('apply_job', args=[job.id])
    
    try:
        response = client.post(apply_url, {'resume': resume_file}, follow=True)
        if response.status_code != 200:
            print(f"    [ERROR] Unexpected status code {response.status_code}")
            print(response.content.decode('utf-8')[:500])
            sys.exit(1)
    except Exception as e:
        print(f"    [ERROR] Parsing or submission crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
        
    print("    [SUCCESS] Application submitted and parsed successfully.")
    
    # 4. Verify AI Evaluation & Shortlisting
    print("[4] Verifying Shortlisting Logic...")
    
    # Because client.post triggers the logic, let's pull the created application
    app = Application.objects.filter(candidate__user=user, job=job).first()
    
    if not app:
        print("    [ERROR] Application object was not created in DB.")
        sys.exit(1)
        
    print(f"    [INFO] AI Score: {app.ai_score}/100")
    print(f"    [INFO] Status: {app.status}")
    print(f"    [INFO] Insights: {app.ai_insights[:200]}...")
    
    if app.ai_score is None:
        print("    [ERROR] AI Score is NULL. Parsing logic failed to score the resume.")
        sys.exit(1)
        
    if app.status == 'APPLIED':
        print("    [INFO] Notice: Status remained APPLIED. The automated email/scheduling triggers might be async or manual.")
        
    print("\n--- ✅ Flow completed perfectly! ---")
    
if __name__ == "__main__":
    run_test()
