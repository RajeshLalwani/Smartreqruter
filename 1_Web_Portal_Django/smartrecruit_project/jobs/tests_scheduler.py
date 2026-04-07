from django.test import TestCase, RequestFactory, override_settings
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from jobs.models import JobPosting, Application, Candidate, Interview
from jobs.views import schedule_interview_view
from datetime import timedelta

User = get_user_model()

@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class SchedulerAutomationTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        
        # Create Recruiter
        self.recruiter = User.objects.create_user(username='recruiter', password='password', is_recruiter=True)
        
        # Create Candidate
        self.candidate_user = User.objects.create_user(username='candidate', password='password')
        self.candidate = Candidate.objects.create(user=self.candidate_user, full_name='John Doe', email='john@example.com')
        
        # Create Job
        self.job = JobPosting.objects.create(
            recruiter=self.recruiter,
            title="Python Dev",
            description="Test Job",
            required_skills="Python",
            location="Remote"
        )
        
        # Create Application
        self.application = Application.objects.create(
            job=self.job,
            candidate=self.candidate,
            status='ROUND_1_PENDING'
        )

    def test_dynamic_slot_generation(self):
        """ Verify slots are generated for candidate view """
        request = self.factory.get(reverse('schedule_interview_view', args=[self.application.id]))
        request.user = self.candidate_user
        
        # Add message support
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        
        response = schedule_interview_view(request, self.application.id)
        
        self.assertEqual(response.status_code, 200)
        # We can't easily check context with RequestFactory as it returns HttpResponse not TemplateResponse usually, 
        # or render() returns HttpResponse.
        # But we can check content.
        self.assertIn(b'Monday', response.content) # Assuming generic day name is in output
        self.assertIn(b'Available', response.content)

    def test_booking_dynamic_slot(self):
        # Pick a valid time (e.g. tomorrow 10am)
        tomorrow = timezone.now() + timedelta(days=1)
        if tomorrow.weekday() >= 5: # If weekend, push to Monday
            tomorrow += timedelta(days=2)
            
        start_time = timezone.make_aware(timezone.datetime.combine(tomorrow.date(), timezone.datetime.min.time().replace(hour=10)))
        
        request = self.factory.post(reverse('schedule_interview_view', args=[self.application.id]), {
            'start_time': start_time.isoformat()
        })
        request.user = self.candidate_user
        
        # Add message support
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        
        response = schedule_interview_view(request, self.application.id)
        
        self.assertEqual(response.status_code, 302)
        
        # Verify Interview Created
        self.assertTrue(Interview.objects.filter(application=self.application, status='SCHEDULED').exists())
        
    def test_expiry_command(self):
        from django.core.management import call_command
        from io import StringIO
        
        # Set updated_at to 8 days ago
        old_date = timezone.now() - timedelta(days=8)
        
        # Hack to update auto_now field
        Application.objects.filter(id=self.application.id).update(updated_at=old_date)
        
        out = StringIO()
        call_command('check_application_expiry', stdout=out)
        
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'REJECTED')
        self.assertIn('Successfully auto-rejected 1 applications', out.getvalue())
