import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartrecruit_project.settings')
django.setup()

from jobs.talent_intelligence import estimate_salary
from jobs.utils import match_resume_with_ai
from jobs.models import JobPosting

def run_tests():
    print("--- Testing Salary Estimator ---")
    salary = estimate_salary(
        job_title="Data Scientist",
        experience_years=4.5,
        skills_text="Python, SQL, Machine Learning, TensorFlow, PyTorch, Natural Language Processing",
        location="Bangalore",
        ai_score=85
    )
    print(f"Salary Estimator Output: {salary['currency']} {salary['salary_min']} - {salary['salary_max']} (Mid: {salary['salary_mid']})")

if __name__ == "__main__":
    run_tests()
