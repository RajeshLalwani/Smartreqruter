from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.template import Context, Template
from core.templatetags.blind_filters import anonymize
from core.models import User

class BlindHiringTests(TestCase):
    def setUp(self):
        self.recruiter = User.objects.create_user(username='recruiter', password='password', is_recruiter=True)
        self.candidate_user = User.objects.create_user(username='candidate', first_name='John', last_name='Doe', is_candidate=True)
        # Create Candidate profile
        from jobs.models import Candidate
        self.candidate = Candidate.objects.create(user=self.candidate_user, full_name='John Doe', email='john@example.com')
        
    def test_anonymize_filter_off(self):
        """Test that filter returns full name when blind hiring is OFF"""
        self.recruiter.blind_hiring = False
        result = anonymize(self.candidate, self.recruiter)
        self.assertEqual(result, "John Doe")

    def test_anonymize_filter_on(self):
        """Test that filter returns masked name when blind hiring is ON"""
        self.recruiter.blind_hiring = True
        result = anonymize(self.candidate, self.recruiter)
        self.assertEqual(result, f"Candidate #{self.candidate.id}")

    def test_settings_toggle(self):
        """Test that settings view toggles the flag"""
        self.client.login(username='recruiter', password='password')
        response = self.client.post('/settings/', {
            'action': 'toggle_blind_hiring',
            'blind_hiring': 'on'
        })
        self.recruiter.refresh_from_db()
        self.assertTrue(self.recruiter.blind_hiring)

        response = self.client.post('/settings/', {
            'action': 'toggle_blind_hiring'
            # 'blind_hiring' missing means off
        })
        self.recruiter.refresh_from_db()
        self.assertFalse(self.recruiter.blind_hiring)
