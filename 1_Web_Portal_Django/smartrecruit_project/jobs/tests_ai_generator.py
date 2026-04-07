from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.auth import get_user_model
from .utils import generate_ai_job_description
from .views import generate_jd_api
import json
from unittest.mock import patch

User = get_user_model()


class AIJDGeneratorTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='recruiter', password='password')
        self.user.is_recruiter = True # Assuming this flag exists or is handled
        self.url = reverse('generate_jd_api')

    def test_utils_generate_ai_job_description(self):
        """Test the utility function generates content with keywords."""
        title = "Python Developer"
        skills = ["Django", "API"]
        jd = generate_ai_job_description(title, skills)
        
        self.assertIn("Python Developer", jd)
        self.assertIn("Django", jd)
        self.assertIn("API", jd)
        self.assertIn("**Job Overview**", jd)

    def test_api_generate_jd_success(self):
        """Test the API endpoint returns success and description."""
        data = {'title': 'Frontend Engineer', 'skills': 'React, CSS', 'tone': 'modern'}
        request = self.factory.post(self.url, json.dumps(data), content_type='application/json')
        request.user = self.user
        
        response = generate_jd_api(request)
        content = json.loads(response.content)
        
        self.assertTrue(content['success'])
        self.assertIn("Frontend Engineer", content['description'])
        self.assertIn("React", content['description'])
        # Check for modern tone indicators
        self.assertTrue(any(x in content['description'] for x in ['collaborative', 'innovation', 'forward-thinking']))

    def test_utils_generate_ai_job_description_tones(self):
        # Test Modern
        desc_modern = generate_ai_job_description("Dev", "Python", "modern")
        # Check for any of the modern intro markers
        self.assertTrue("collaborative team" in desc_modern or "forward-thinking team" in desc_modern)

        # Test Dynamic
        desc_dynamic = generate_ai_job_description("Dev", "Python", "dynamic")
        # Check for any of the dynamic intro markers
        self.assertTrue("fast-paced environment" in desc_dynamic or "scaling rapidly" in desc_dynamic)

        # Test Professional (default or explicit)
        desc_prof = generate_ai_job_description("Dev", "Python", "professional")
        self.assertTrue("Job Title:" in desc_prof or "highly qualified" in desc_prof or "established company" in desc_prof)


    def test_api_generate_jd_invalid_method(self):
        """Test API rejects GET requests."""
        request = self.factory.get(self.url)
        request.user = self.user
        
        response = generate_jd_api(request)
        content = json.loads(response.content)
        
        self.assertFalse(content['success'])
        self.assertEqual(content['error'], 'POST request required')
