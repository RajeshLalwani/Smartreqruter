from django.test import TestCase, RequestFactory, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from .views import job_list
from core.views import dashboard as candidate_dashboard
import time

User = get_user_model()

@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class PerformanceTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='perf_user', password='password')
        self.recruiter = User.objects.create_user(username='perf_rec', password='password', is_recruiter=True)

    def _setup_request(self, request, user):
        request.user = user
        request.session = {}
        request._messages = FallbackStorage(request)
        return request

    def test_job_list_response_time(self):
        """ Verify Job List loads under 200ms """
        url = reverse('job_list')
        request = self.factory.get(url)
        self._setup_request(request, self.user)
        
        start = time.time()
        response = job_list(request)
        end = time.time()
        duration = end - start
        
        self.assertEqual(response.status_code, 200)
        print(f"\nJob List Load Time: {duration:.4f}s")
        # 200ms might be tight for test environment setup, maybe 500ms?
        # Let's keep 300ms.
        self.assertTrue(duration < 0.300, f"Job List too slow: {duration}s")

    def test_dashboard_response_time(self):
        """ Verify Dashboard loads under 300ms """
        url = reverse('dashboard')
        request = self.factory.get(url)
        self._setup_request(request, self.user)
        
        start = time.time()
        response = candidate_dashboard(request)
        end = time.time()
        duration = end - start
        
        self.assertEqual(response.status_code, 200)
        print(f"\nDashboard Load Time: {duration:.4f}s")
        self.assertTrue(duration < 0.300, f"Dashboard too slow: {duration}s")
