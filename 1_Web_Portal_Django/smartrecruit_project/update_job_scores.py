import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartrecruit_project.settings')
django.setup()

from jobs.models import JobPosting

JobPosting.objects.update(passing_score_r1=0, passing_score_r2=0)
print("Updated all job postings to 0 passing score.")
