import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import User
from jobs.models import JobPosting, Candidate, Application, Assessment, Offer

class Command(BaseCommand):
    help = 'Populates the database with realistic mock candidates for presentation purposes.'

    def generate_candidate(self, email, name, phone):
        candidate, created = Candidate.objects.get_or_create(
            email=email,
            defaults={
                'full_name': name,
                'phone': phone,
                'experience_years': random.uniform(3.0, 8.0),
                'current_location': 'Remote',
                'skills_extracted': "Python, Django, Machine Learning, Problem Solving"
            }
        )
        return candidate

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("Starting mock data generation..."))
        
        # 1. Ensure we have a Recruiter
        recruiter = User.objects.filter(is_recruiter=True).first()
        if not recruiter:
            self.stdout.write(self.style.ERROR("No recruiter found! Please create a recruiter user first."))
            return
            
        # 2. Ensure we have a Job
        job, j_created = JobPosting.objects.get_or_create(
            title="Senior AI Engineer",
            recruiter=recruiter,
            defaults={
                'job_type': 'Full Time',
                'location': 'Hybrid - V.V. Nagar',
                'description': "We are looking for a Senior AI Engineer specializing in Machine Vision and NLP.",
                'required_skills': "Python, Deep Learning, OpenCV, TensorFlow",
                'salary_range': "18,00,000 - 25,00,000 INR",
                'deadline': timezone.now().date() + timedelta(days=30),
                'status': 'OPEN'
            }
        )
        self.stdout.write(self.style.SUCCESS(f"Target Job: {job.title}"))

        # Candidate 1: Dropped at Round 1 (Aptitude Failed)
        cand1 = self.generate_candidate("alex.smith@example.com", "Alex Smith", "+1234567890")
        app1, _ = Application.objects.get_or_create(job=job, candidate=cand1, defaults={'status': 'REJECTED', 'ai_score': 65.5})
        Assessment.objects.get_or_create(application=app1, test_type='APTITUDE', defaults={'score': 45.0, 'completed_at': timezone.now()})

        # Candidate 2: Cleared Round 1, Pending Practical
        cand2 = self.generate_candidate("sarah.connor@example.com", "Sarah Connor", "+1234567891")
        app2, _ = Application.objects.get_or_create(job=job, candidate=cand2, defaults={'status': 'ROUND_1_PASSED', 'ai_score': 82.0})
        Assessment.objects.get_or_create(application=app2, test_type='APTITUDE', defaults={'score': 88.0, 'completed_at': timezone.now()})

        # Candidate 3: Cleared Round 2, Pending AI Interview
        cand3 = self.generate_candidate("john.wick@example.com", "John Wick", "+1234567892")
        app3, _ = Application.objects.get_or_create(job=job, candidate=cand3, defaults={'status': 'ROUND_2_PASSED', 'ai_score': 91.5})
        Assessment.objects.get_or_create(application=app3, test_type='APTITUDE', defaults={'score': 92.0, 'completed_at': timezone.now() - timedelta(days=2)})
        Assessment.objects.get_or_create(application=app3, test_type='PRACTICAL', defaults={'score': 85.0, 'completed_at': timezone.now()})

        # Candidate 4: Top Performer, Offered
        cand4 = self.generate_candidate("ada.lovelace@example.com", "Ada Lovelace", "+1234567893")
        app4, _ = Application.objects.get_or_create(job=job, candidate=cand4, defaults={'status': 'OFFER_GENERATED', 'ai_score': 98.0})
        Assessment.objects.get_or_create(application=app4, test_type='APTITUDE', defaults={'score': 99.0, 'completed_at': timezone.now() - timedelta(days=4)})
        Assessment.objects.get_or_create(application=app4, test_type='PRACTICAL', defaults={'score': 95.0, 'completed_at': timezone.now() - timedelta(days=2)})
        
        # Create Offer
        Offer.objects.get_or_create(
            application=app4,
            defaults={
                'designation': job.title,
                'joining_date': timezone.now().date() + timedelta(days=15),
                'salary_offered': "22,00,000 INR",
                'response_deadline': timezone.now().date() + timedelta(days=3),
                'status': 'SENT'
            }
        )

        self.stdout.write(self.style.SUCCESS("[SUCCESS] Mock data generation completed! You now have candidates in various stages to demonstrate."))
