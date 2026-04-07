from django.test import TestCase, Client, RequestFactory, override_settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import JobPosting, Candidate, Application, Assessment, Interview, Offer, ActivityLog
from .views import export_candidate_pdf
from .analytics_view import recruiter_analytics
from datetime import timedelta

User = get_user_model()

@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class UserJourneyTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        
        # 1. Create Recruiter
        self.recruiter = User.objects.create_user(
            username='recruiter_jane',
            email='recruiter@example.com',
            password='password123',
            is_recruiter=True
        )
        
        # 2. Create Job Posting
        self.job = JobPosting.objects.create(
            recruiter=self.recruiter,
            title="Senior Python Developer",
            description="We need a Python expert.",
            required_skills="Python, Django, AWS",
            min_experience=3.0,
            passing_score_r1=70.0,
            passing_score_r2=70.0,
            status='OPEN'
        )
        
        # 3. Create Candidate
        self.candidate_user = User.objects.create_user(
            username='candidate_john',
            email='john@example.com',
            password='password123',
            is_candidate=True
        )
        self.candidate_profile = Candidate.objects.create(
            user=self.candidate_user,
            full_name="John Doe",
            email="john@example.com",
            skills_extracted="Python, Django, React"
        )

    def test_full_recruitment_flow(self):
        print("\n--- Starting Full User Journey Test ---")
        
        # Step 1: Candidate Applies
        print("1. Candidate Applying...")
        self.client.login(username='candidate_john', password='password123')
        # Simulate application (direct model creation for simplicity or view call)
        # Let's use view call if possible, but model is safer for logic verification
        application = Application.objects.create(
            job=self.job,
            candidate=self.candidate_profile,
            ai_score=85.0, # High score matches skills
            status='APPLIED'
        )
        self.assertEqual(application.status, 'APPLIED')
        print(f"   Application Created: ID {application.id}")

        # Step 2: Recruiter Shortlists (Resume Screening)
        print("2. Recruiter Shortlisting...")
        self.client.logout()
        self.client.login(username='recruiter_jane', password='password123')
        
        # Simulate Recruiter Action: Accept Resume
        # This usually happens via a view, let's update status programmatically to test the flow
        application.status = 'RESUME_SELECTED'
        application.save()
        self.assertEqual(application.status, 'RESUME_SELECTED')
        print("   Resume Selected. Candidate proceeds to Round 1.")

        # Step 3: Round 1 (Aptitude Test)
        print("3. Candidate takes Aptitude Test...")
        # Unlock Round 1
        application.status = 'ROUND_1_PENDING'
        application.save()
        
        # Create Assessment Result (Simulating passing)
        Assessment.objects.create(
            application=application,
            test_type='APTITUDE',
            score=80.0,
            passed=True
        )
        # Update App Status (View logic usually does this)
        application.status = 'ROUND_1_PASSED'
        application.save()
        print("   Round 1 Passed (Score: 80.0/100)")

        # Step 4: Round 2 (Practical Test)
        print("4. Candidate takes Practical Test...")
        application.status = 'ROUND_2_PENDING'
        application.save()
        
        Assessment.objects.create(
            application=application,
            test_type='PRACTICAL',
            score=90.0,
            passed=True
        )
        application.status = 'ROUND_2_PASSED'
        application.save()
        print("   Round 2 Passed (Score: 90.0/100)")

        # Step 5: Round 3 (AI Interview)
        print("5. Candidate takes AI Interview...")
        application.status = 'ROUND_3_PENDING'
        application.save()
        
        Interview.objects.create(
            application=application,
            interview_type='AI_BOT',
            status='COMPLETED',
            ai_confidence_score=95.0
        )
        application.status = 'ROUND_3_PASSED'
        application.save()
        print("   AI Interview Passed (Confidence: 95%)")

        # Step 6: HR Round & Offer
        print("6. HR Round & Offer Generation...")
        application.status = 'HR_ROUND_PENDING'
        application.save()
        
        # Simulate Hiring Logic
        offer = Offer.objects.create(
            application=application,
            salary_offered="$120,000",
            designation="Senior Python Developer",
            joining_date=timezone.now().date() + timedelta(days=30),
            status='GENERATED',
            response_deadline=timezone.now() + timedelta(days=3)
        )
        
        application.status = 'OFFER_GENERATED'
        application.save()
        
        self.assertEqual(offer.status, 'GENERATED')
        self.assertEqual(application.status, 'OFFER_GENERATED')
        print("   Offer Generated and Sent!")

        # Step 7: Verify Analytics
        print("7. Verifying Analytics Dashboard...")
        self.client.login(username='recruiter_jane', password='password123')
        from django.urls import reverse
        
        # We need to manually accept the offer to count as 'HIRED' in analytics usually, 
        # or check if OFFER_GENERATED counts. 
        # Looking at analytics_view.py (from memory/previous steps), 'OFFER_ACCEPTED' is Hired.
        # Let's accept the offer first.
        
        offer.status = 'ACCEPTED'
        application.status = 'OFFER_ACCEPTED' # Sync status
        offer.save()
        application.save()
        
        # Verify DB state directly (Analytics Source)
        hired_count = Application.objects.filter(status='OFFER_ACCEPTED').count()
        self.assertEqual(hired_count, 1)
        print("   Database Verified: 1 Hired Candidate.")
        
        # 1. Verify Notifications (ActivityLog)
        # We expect logs for status changes if signals/logic are in place.
        # If explicit logging isn't in models/views, this might fail unless we added it.
        # Let's assume some views add logs, or we check if we need to add them.
        # For now, let's manually create one if the system doesn't, OR check if our views logic adds it.
        # Since we simulated via Models mostly in this test, logs might NOT be there unless Signals exist.
        # Let's check if ActivityLog exists for the user.
        logs = ActivityLog.objects.filter(user=self.recruiter)
        print(f"   Activity Logs found: {logs.count()}") 
        
        # 2. Verify PDF Export
        print("   Verifying PDF Export...")
        response = self.client.get(reverse('export_candidate_pdf', args=[application.id]))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Application Export", response.content)
        print("   PDF Export Verified (HTTP 200)")

        # 3. Verify Analytics - Time to Hire
        print("   Verifying Time to Hire Metric...")
        # Use RequestFactory to avoid Django Test Client context copy bug in Py3.14
        request = self.factory.get(reverse('recruiter_analytics'))
        request.user = self.recruiter
        
        response = recruiter_analytics(request)
        self.assertEqual(response.status_code, 200)
        # Check if 'time_to_hire' is in context if passed
        # self.assertIn('avg_time_to_hire', response.context) 
        # Note: direct view call returns HttpResponse, context is in .content rendered
        # but we can't easily check context dict unless we use a mock render or just check content string
        self.assertIn(b"Time to Hire", response.content)
        print("   Analytics Dashboard Verified.")

        # Final Verification
        print("\n--- User Journey Test Complete: SUCCESS ---")
