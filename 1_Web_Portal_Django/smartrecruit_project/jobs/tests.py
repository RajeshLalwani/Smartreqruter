from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core import mail
from django.conf import settings
from unittest.mock import patch, MagicMock
import json
import os
import asyncio

from jobs.models import JobPosting, Application, Candidate
from jobs.views import get_notifications_api, export_candidate_pdf
# Adjust import based on actual path. 
# Previously checks showed 'Interview_Bot.interviewer' is correct.
try:
    from Interview_Bot.interviewer import AIInterviewer
except ImportError:
    AIInterviewer = None

User = get_user_model()

class AIInterviewerTests(TestCase):
    def setUp(self):
        if not AIInterviewer:
            self.skipTest("AIInterviewer module not found")
        self.interviewer = AIInterviewer()


    def test_analyze_sentiment_positive(self):
        # Mock textblob module in sys.modules
        mock_blob_module = MagicMock()
        mock_blob_class = MagicMock()
        mock_blob_instance = MagicMock()
        
        mock_blob_instance.sentiment.polarity = 0.8
        mock_blob_instance.sentiment.subjectivity = 0.5
        mock_blob_class.return_value = mock_blob_instance
        mock_blob_module.TextBlob = mock_blob_class
        
        with patch.dict('sys.modules', {'textblob': mock_blob_module}):
             # Re-instantiate or ensure import happens here?
             # The import is inside the method, so calling it now should trigger the import from sys.modules
             # Added "team" to trigger keyword bonus (+20), total should be 60.
             score = self.interviewer.analyze_hr_response("I am very excited about this opportunity and want to join the team!")['score']
        
        # We need to verify the score logic.
        # Logic: polarity > 0.5 -> +30.
        # subjectivity > 0.2 -> +10.
        # "team" -> +20.
        # Total = 60.
        # Min score is 40.
        self.assertGreater(score, 40)


    def test_analyze_sentiment_negative(self):
        # Mock textblob module
        mock_blob_module = MagicMock()
        mock_blob_class = MagicMock()
        mock_blob_instance = MagicMock()
        
        mock_blob_instance.sentiment.polarity = -0.5
        mock_blob_instance.sentiment.subjectivity = 0.5 # Still high subjectivity
        mock_blob_class.return_value = mock_blob_instance
        mock_blob_module.TextBlob = mock_blob_class
        
        with patch.dict('sys.modules', {'textblob': mock_blob_module}):
             res = self.interviewer.analyze_hr_response("This is bad.")
        
        # Logic: polarity < -0.1 -> score += 10.
        self.assertGreater(res['score'], 0) # Just ensure it doesn't crash

class UtilsTests(TestCase):
    @patch('jobs.utils.asyncio.run')
    @patch('jobs.utils._generate_voice_async')
    def test_generate_voice_file(self, mock_gen_async, mock_asyncio_run):
        from jobs.utils import generate_voice_file
        
        # Mock _generate_voice_async to return None (not a coroutine)
        # So asyncio.run(None) happens
        mock_gen_async.return_value = None
        mock_asyncio_run.return_value = None

        text = "Hello, this is a test."
        result = generate_voice_file(text)
        
        self.assertIsNotNone(result)
        self.assertTrue(result.startswith('voice_questions'))
        self.assertTrue(result.endswith('.mp3'))
        
        # Verify call arguments
        mock_gen_async.assert_called_once()


    @patch('jobs.email_utils.EmailMultiAlternatives')
    def test_send_html_email(self, mock_email):
        from jobs.email_utils import send_html_email
        
        mock_email_instance = MagicMock()
        mock_email.return_value = mock_email_instance

        subject = "Test Subject"
        template = "jobs/test_email.html" # Needs to exist or handled
        context = {'name': 'John'}
        recipient = "test@example.com"

        # We need to make sure render_to_string works or mock it too
        with patch('jobs.email_utils.render_to_string', return_value="<html>Hi John</html>"):
            result = send_html_email(subject, template, context, recipient)
        
        self.assertTrue(result)
        mock_email_instance.send.assert_called_once()

class ViewsTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.recruiter = User.objects.create_user(username='recruiter', password='password', is_recruiter=True)

    def test_get_notifications_api(self):
        from jobs.models import Notification
        # Create some notifications
        Notification.objects.create(user=self.user, title="N1", message="Applied to Job A")
        Notification.objects.create(user=self.user, title="N2", message="Profile Updated")

        request = self.factory.get(reverse('get_notifications_api'))
        request.user = self.user
        
        response = get_notifications_api(request)
        self.assertEqual(response.status_code, 200)
        
        content = json.loads(response.content)
        self.assertEqual(content['unread_count'], 2)
        self.assertEqual(len(content['notifications']), 2)
        self.assertEqual(content['notifications'][0]['message'], "Profile Updated") # Most recent first

    def test_export_candidate_pdf(self):
        # create data
        job = JobPosting.objects.create(recruiter=self.recruiter, title="Dev", description="Desc")
        candidate = Candidate.objects.create(user=self.user, full_name="Test Cand", email="t@t.com")
        app = Application.objects.create(job=job, candidate=candidate)

        request = self.factory.get(reverse('export_candidate_pdf', args=[app.id]))
        request.user = self.user # Own application
        
        response = export_candidate_pdf(request, app.id)
        self.assertEqual(response.status_code, 200)
        # Check basic HTML content presence
        self.assertIn(b"Application Export", response.content)
