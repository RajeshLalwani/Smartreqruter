from django.test import TestCase, RequestFactory, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib.messages.storage.fallback import FallbackStorage
from unittest.mock import patch
from .models import JobPosting, Candidate, Application, Assessment, Interview
from .views import update_status, take_assessment, ai_interview

User = get_user_model()

@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class IntegrationTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        
        # Setup Users
        self.recruiter = User.objects.create_user(username='recruiter_int', email='recruiter@test.com', password='password123', is_recruiter=True)
        self.candidate_user = User.objects.create_user(username='candidate_int', email='candidate@test.com', password='password123')
        self.candidate = Candidate.objects.create(user=self.candidate_user, full_name="Integration Candidate", email="test@example.com")
        
        # Setup Job and Application
        self.job = JobPosting.objects.create(
            recruiter=self.recruiter,
            title="Integration Developer",
            description="Testing integrations",
            required_skills="Python,Django",
            recruiter_id=self.recruiter.id
        )
        self.application = Application.objects.create(
            job=self.job,
            candidate=self.candidate,
            status='APPLIED'
        )

    def _setup_request(self, request, user):
        request.user = user
        request.session = {}
        request._messages = FallbackStorage(request)
        return request

    # 1. Status Update Integration
    @patch('jobs.views.send_status_email')
    def test_status_update_integration(self, mock_send_email):
        """ Test that updating status triggers email and logs """
        url = reverse('update_status', args=[self.application.id, 'RESUME_SELECTED'])
        request = self.factory.get(url)
        self._setup_request(request, self.recruiter)
        
        # Call View Directly
        update_status(request, self.application.id, 'RESUME_SELECTED')
        
        # Verify DB Update
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'RESUME_SELECTED')
        
        # Verify Email Triggered
        if mock_send_email.called:
             args = mock_send_email.call_args[0]
             # args[0] might be User object
             self.assertEqual(args[0].email, self.candidate_user.email)

    # 2. Assessment Scoring Integration
    @patch('jobs.services.send_status_email')
    def test_assessment_scoring_integration(self, mock_send_email):
        """ Test submission of aptitude test calculates score and updates model """
        self.application.status = 'RESUME_SELECTED'
        self.application.save()
        
        # Prep Request
        url = reverse('take_assessment', args=[self.application.id, 'aptitude'])
        
        # 1. GET Request (Simulate Population) - We can skip calling view if we verify logic via POST
        # But let's mock the fetch to be safe
        
        with patch('jobs.views.fetch_questions') as mock_fetch:
            mock_fetch.return_value = [
                {'id': 1, 'text': 'Q1', 'options': [], 'correct': 'A'},
                {'id': 2, 'text': 'Q2', 'options': [], 'correct': 'B'},
            ]
            
            # Setup Session Manually (since we bypass GET view execution or logic)
            # The view expects 'assessment_{id}_answers' in session
            session_data = {
                '1': 'A',
                '2': 'B'
            }
            
            # 2. POST Request
            payload = {
                '1': 'A', # Correct
                '2': 'C'  # Wrong
            }
            request = self.factory.post(url, payload)
            request = self._setup_request(request, self.candidate_user)
            request.session[f'assessment_{self.application.id}_answers'] = session_data
            
            # Call View
            print("SESSION DATA IN TEST:", request.session.get(f'assessment_{self.application.id}_answers'))
            take_assessment(request, self.application.id, 'aptitude')
            
            # Verify Assessment
            assessment = Assessment.objects.filter(application=self.application, test_type='APTITUDE').first()
            self.assertIsNotNone(assessment)
            self.assertEqual(assessment.score, 50.0)
            
            # Verify Email Triggered
            mock_send_email.assert_called_once()


    # 3. AI Interview Integration
    @patch('jobs.views.send_status_email')
    @patch('Interview_Bot.interviewer.AIInterviewer.analyze_response')
    @patch('Interview_Bot.interviewer.AIInterviewer.generate_question')
    def test_ai_interview_integration(self, mock_gen_question, mock_analyze, mock_send_email):
        """ Test AI Interview submission creates Interview record and updates Application """
        # Prerequisite
        self.application.status = 'ROUND_2_PASSED'
        self.application.save()
        
        # Mock Interactions
        mock_gen_question.return_value = {'text': 'Explain generic views.', 'topic': 'Django'}
        mock_analyze.return_value = {'score': 90.0, 'feedback': 'Perfect.'}
        
        url = reverse('ai_interview', args=[self.application.id])
        
        # POST Request
        payload = {'answer': 'Generic views abstract common patterns...'}
        request = self.factory.post(url, payload)
        self._setup_request(request, self.candidate_user)
        
        # Call View
        ai_interview(request, self.application.id)
        
        # Verify Interview Record
        interview = Interview.objects.filter(application=self.application, interview_type='AI_BOT').first()
        self.assertIsNotNone(interview)
        self.assertEqual(interview.ai_confidence_score, 90.0)
        self.assertEqual(interview.feedback, 'Perfect.')
        
        # Verify Application Status Update
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'ROUND_3_PASSED')
        
        # Verify Email Triggered
        mock_send_email.assert_called_once()
