from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from jobs.models import JobPosting, Candidate, Application
from jobs.security import get_authorized_application
from django.core.exceptions import PermissionDenied

User = get_user_model()

class RBACSecurityTests(TestCase):
    def setUp(self):
        # Create users
        self.recruiter_owner = User.objects.create_user(username='recruiter_owner', password='password123', is_recruiter=True)
        self.recruiter_other = User.objects.create_user(username='recruiter_other', password='password123', is_recruiter=True)
        self.candidate_owner = User.objects.create_user(username='candidate_owner', password='password123')
        self.candidate_other = User.objects.create_user(username='candidate_other', password='password123')
        
        # Create candidate profiles
        self.cand_owner_profile = Candidate.objects.create(user=self.candidate_owner, full_name="Owner Candidate")
        self.cand_other_profile = Candidate.objects.create(user=self.candidate_other, full_name="Other Candidate")
        
        # Create Job
        self.job = JobPosting.objects.create(
            recruiter=self.recruiter_owner,
            title="Secure Job",
            job_type="FULL_TIME",
            location="Remote"
        )
        
        # Create Application
        self.application = Application.objects.create(
            job=self.job,
            candidate=self.cand_owner_profile,
            status="RESUME_SCREENING"
        )
        
    def test_authorized_recruiter(self):
        """Owning recruiter should be able to access the application"""
        class MockRequest:
            user = self.recruiter_owner
        
        app = get_authorized_application(MockRequest(), self.application.id)
        self.assertEqual(app, self.application)

    def test_unauthorized_recruiter(self):
        """Other recruiter should be blocked"""
        class MockRequest:
            user = self.recruiter_other
            
        with self.assertRaises(PermissionDenied):
            get_authorized_application(MockRequest(), self.application.id)
            
    def test_authorized_candidate(self):
        """Owning candidate should be able to access"""
        class MockRequest:
            user = self.candidate_owner
            
        app = get_authorized_application(MockRequest(), self.application.id)
        self.assertEqual(app, self.application)
        
    def test_unauthorized_candidate(self):
        """Other candidate should be blocked from IDOR"""
        class MockRequest:
            user = self.candidate_other
            
        with self.assertRaises(PermissionDenied):
            get_authorized_application(MockRequest(), self.application.id)

    def test_strict_role_enforcement_recruiter(self):
        """Candidate should be blocked if require_role='recruiter'"""
        class MockRequest:
            user = self.candidate_owner
            
        with self.assertRaises(PermissionDenied):
            get_authorized_application(MockRequest(), self.application.id, require_role='recruiter')
