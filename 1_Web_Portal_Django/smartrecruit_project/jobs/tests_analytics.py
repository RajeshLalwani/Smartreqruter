from django.test import TestCase, override_settings, RequestFactory
from django.urls import reverse
from django.contrib.auth import get_user_model
from jobs.models import JobPosting, Candidate, Application
from django.utils import timezone
import datetime
from django.contrib.messages.storage.fallback import FallbackStorage
from jobs.analytics_view import recruiter_analytics
from jobs.views_analytics_export import export_analytics_csv_view

User = get_user_model()

@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class AnalyticsTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.recruiter = User.objects.create_user(username='recruiter_test', password='password', is_recruiter=True)
        
        self.job = JobPosting.objects.create(
            recruiter=self.recruiter,
            title="Software Engineer",
            description="Test Job",
            required_skills="Python",
            location="Remote"
        )
        
        # Create Candidates
        c1 = User.objects.create_user(username='c1', password='pw', is_candidate=True)
        cand1 = Candidate.objects.create(user=c1, full_name="C1", email="c1@test.com", experience_years=1, current_location="New York")
        
        c2 = User.objects.create_user(username='c2', password='pw', is_candidate=True)
        cand2 = Candidate.objects.create(user=c2, full_name="C2", email="c2@test.com", experience_years=4, current_location="London")
        
        # Create Applications
        a1 = Application.objects.create(job=self.job, candidate=cand1, source_of_hire='LINKEDIN')
        a1.applied_at = timezone.now() - datetime.timedelta(days=10) # 10 days ago
        a1.save()
        
        a2 = Application.objects.create(job=self.job, candidate=cand2, source_of_hire='WEBSITE')
        a2.applied_at = timezone.now() # Today
        a2.save()

    def test_analytics_view(self):
        request = self.factory.get(reverse('recruiter_analytics'))
        request.user = self.recruiter
        # Mock messages
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        
        response = recruiter_analytics(request)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        
        self.assertIn('LinkedIn', content)
        self.assertIn('London', content)

    def test_analytics_filtering(self):
        today = timezone.now().date()
        request = self.factory.get(reverse('recruiter_analytics'), {
            'start_date': today,
            'end_date': today
        })
        request.user = self.recruiter
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        
        response = recruiter_analytics(request)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        
        # If filtering works, "LinkedIn" (10 days ago) should NOT be in the source keys for today!
        self.assertNotIn('LinkedIn', content)
        self.assertIn('Career Site', content) # Website mapped to Career Site

    def test_export_csv(self):
        request = self.factory.get(reverse('export_analytics_csv'))
        request.user = self.recruiter
        
        response = export_analytics_csv_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        
        content = response.content.decode('utf-8')
        # Total apps = 2 (no filter)
        self.assertIn('Total Applications,2', content.replace('\r', ''))
        self.assertIn('LinkedIn', content)

    def test_export_csv_filtered(self):
        today = timezone.now().date()
        request = self.factory.get(reverse('export_analytics_csv'), {
            'start_date': today,
            'end_date': today
        })
        request.user = self.recruiter
        
        response = export_analytics_csv_view(request)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        
        # Total apps = 1 (filtered)
        self.assertIn('Total Applications,1', content.replace('\r', ''))
        self.assertNotIn('LinkedIn', content)

    def test_export_pdf(self):
        from jobs.views_analytics_export import export_analytics_pdf_view
        request = self.factory.get(reverse('export_analytics_pdf'))
        request.user = self.recruiter
        
        response = export_analytics_pdf_view(request)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        
        # Verify HTML structure
        self.assertIn('<html>', content)
        self.assertIn('window.print()', content)
        self.assertIn('Recruitment Analytics Report', content)
