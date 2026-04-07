from django.test import TestCase, RequestFactory, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.authtoken.models import Token
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import Http404, HttpResponseRedirect
from django.core.exceptions import PermissionDenied
from .models import JobPosting, Application, Candidate, Technology
from .models import JobPosting, Application, Candidate, Technology
from .views import (
    candidate_list, take_assessment, 
    ai_interview, post_job, job_detail
)
from .analytics_view import recruiter_analytics
from .views_advanced import smart_question_generator, ai_email_drafter

User = get_user_model()

@override_settings(
    STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage',
    SECURE_SSL_REDIRECT=False,
)
class SecurityTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        
        # Users
        self.recruiter = User.objects.create_user(username='recruiter_sec', password='password', is_recruiter=True)
        self.other_recruiter = User.objects.create_user(username='other_recruiter', password='password', is_recruiter=True)
        self.candidate_a = User.objects.create_user(username='candidate_a', password='password')
        self.candidate_b = User.objects.create_user(username='candidate_b', password='password')
        self.candidate_c = User.objects.create_user(username='candidate_c', password='password')
        
        self.profile_a = Candidate.objects.create(user=self.candidate_a, full_name="Alice", email="alice@test.com")
        self.profile_b = Candidate.objects.create(user=self.candidate_b, full_name="Bob", email="bob@test.com")
        self.profile_c = Candidate.objects.create(user=self.candidate_c, full_name="Carol", email="carol@test.com")
        
        # Job & Applications
        self.job = JobPosting.objects.create(recruiter=self.recruiter, title="Secure Job", description="Desc")
        self.other_job = JobPosting.objects.create(recruiter=self.other_recruiter, title="Other Job", description="Desc")
        
        self.app_a = Application.objects.create(job=self.job, candidate=self.profile_a, status='APPLIED')
        self.app_b = Application.objects.create(job=self.job, candidate=self.profile_b, status='APPLIED')
        self.other_app = Application.objects.create(job=self.other_job, candidate=self.profile_b, status='HIRED')
        self.own_hired_app = Application.objects.create(job=self.job, candidate=self.profile_c, status='HIRED')

    def _setup_request(self, request, user):
        request.user = user
        request.session = {}
        request._messages = FallbackStorage(request)
        return request

    # 1. RBAC: Candidate cannot access Recruiter Views
    def test_rbac_candidate_access_recruiter_analytics(self):
        """ Verify candidate cannot access recruiter analytics """
        url = reverse('recruiter_analytics')
        request = self.factory.get(url)
        self._setup_request(request, self.candidate_a)
        
        response = recruiter_analytics(request)
        
        # Should redirect to dashboard (based on checks in view)
        self.assertEqual(response.status_code, 302)
        self.assertTrue('/dashboard' in response.url)

    def test_rbac_candidate_access_candidate_list(self):
        """ Verify candidate cannot access candidate list """
        url = reverse('candidate_list')
        request = self.factory.get(url)
        self._setup_request(request, self.candidate_a)
        
        # After we fix views.py, this should redirect
        response = candidate_list(request)
        self.assertEqual(response.status_code, 302)
        self.assertTrue('/dashboard' in response.url)

    # 2. IDOR: Candidate A cannot access Candidate B's Application Status/Details
    def test_idor_candidate_access_other_application(self):
        """ Verify Candidate A cannot access Candidate B's assessment or details """
        # Try to take assessment for App B
        url = reverse('take_assessment', args=[self.app_b.id, 'aptitude'])
        request = self.factory.get(url)
        self._setup_request(request, self.candidate_a)
        
        # Should raise Http404
        with self.assertRaises(Http404):
            take_assessment(request, self.app_b.id, 'aptitude')

    def test_idor_candidate_access_other_interview(self):
        """ Verify Candidate A cannot access Candidate B's AI interview """
        url = reverse('ai_interview', args=[self.app_b.id])
        request = self.factory.get(url)
        self._setup_request(request, self.candidate_a)
        
        with self.assertRaises(Http404):
            ai_interview(request, self.app_b.id)
        
    # 3. Input Validation / Security
    def test_xss_protection_in_job_posting(self):
        """ Verify XSS injection in Job Posting is escaped """
        xss_payload = "<script>alert('XSS')</script>"
        
        # 1. Post Job
        url = reverse('post_job')
        data = {
            'title': xss_payload,
            'description': 'Test',
            'required_skills': 'Python',
            'location': 'Remote',
            'salary_range': '100k',
            'job_type': 'FULL_TIME',
            'technology_stack': 'PYTHON',
            'min_experience': 1.0,
            'passing_score_r1': 70.0,
            'passing_score_r2': 70.0,
            'deadline': '2025-12-31',
            'aptitude_difficulty': 'medium',
            'practical_difficulty': 'medium'
        }
        request = self.factory.post(url, data)
        self._setup_request(request, self.recruiter)
        
        post_job(request)
        
        # 2. View Job
        job = JobPosting.objects.last()
        self.assertEqual(job.title, xss_payload) # DB stores raw
        
        url_detail = reverse('job_detail', args=[job.id])
        request_get = self.factory.get(url_detail)
        self._setup_request(request_get, self.candidate_a) # Viewer
        
        response = job_detail(request_get, job.id)
        
        # Verify Escaping
        content = response.content.decode('utf-8')
        
        self.assertIn("&lt;script&gt;", content)
        self.assertNotIn("<script>alert", content)

    def test_hrms_export_blocks_non_recruiter(self):
        token = Token.objects.create(user=self.candidate_a)
        url = reverse('hrms_export_api')
        response = self.client.get(url, HTTP_AUTHORIZATION=f'Token {token.key}')

        self.assertEqual(response.status_code, 403)

    def test_hrms_export_only_returns_current_recruiters_hires(self):
        token = Token.objects.create(user=self.recruiter)
        url = reverse('hrms_export_api')
        response = self.client.get(url, HTTP_AUTHORIZATION=f'Token {token.key}')

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        returned_ids = {item['application_id'] for item in payload['results']}

        self.assertIn(self.own_hired_app.id, returned_ids)
        self.assertNotIn(self.other_app.id, returned_ids)

    def test_smart_question_generator_ignores_foreign_records(self):
        url = reverse('smart_question_gen')
        request = self.factory.post(url, {
            'job_id': self.other_job.id,
            'application_id': self.other_app.id,
            'focus': 'all',
            'difficulty': 'medium',
            'count': 2,
        })
        self._setup_request(request, self.recruiter)
        response = smart_question_generator(request)

        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertNotIn('Other Job', content)
        self.assertNotIn(f'<option value="{self.other_app.id}">Bob — Other Job</option>', content)

    def test_ai_email_drafter_ignores_foreign_application(self):
        url = reverse('ai_email_drafter')
        request = self.factory.post(url, {
            'application_id': self.other_app.id,
            'email_type': 'shortlist',
        })
        self._setup_request(request, self.recruiter)
        response = ai_email_drafter(request)

        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertNotIn('Other Job', content)
        self.assertNotIn(f'<option value="{self.other_app.id}">Bob — Other Job</option>', content)

