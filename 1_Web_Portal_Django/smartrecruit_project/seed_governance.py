import os
import django
import json
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartrecruit_project.settings')
django.setup()

from jobs.models import QuestionBank
from django.contrib.auth import get_user_model
User = get_user_model()
admin_user = User.objects.filter(is_superuser=True).first()

def seed_governance_data():
    questions = [
        {
            'round': 'ROUND_1_TECHNICAL',
            'category': 'PYTHON',
            'text': 'What is the purpose of __init__ in Python classes?',
            'options': ['Constructor', 'Destructor', 'Decorator', 'Generator'],
            'correct': 'Constructor',
            'attempts': 10,
            'fails': 2 # Normal
        },
        {
            'round': 'ROUND_1_LOGICAL',
            'category': 'MATH',
            'text': 'Solve: 5 + 5 * 5 - 5',
            'options': ['45', '25', '20', '50'],
            'correct': '25',
            'attempts': 20,
            'fails': 15 # High failure (75%) -> BIAS ALERT
        },
        {
            'round': 'ROUND_2_TECHNICAL',
            'category': 'DJANGO',
            'text': 'What is the default port for Django dev server?',
            'options': ['8080', '3000', '8000', '5000'],
            'correct': '8000',
            'attempts': 8,
            'fails': 6 # High failure (75%) -> BIAS ALERT
        },
        {
            'round': 'ROUND_1_TECHNICAL',
            'category': 'SYSTEM',
            'text': 'What does CPU stand for?',
            'options': ['Central Processing Unit', 'Computer Personal Unit', 'Central Power Unit', 'Core Process Unit'],
            'correct': 'Central Processing Unit',
            'attempts': 100,
            'fails': 5 # Very Easy
        }
    ]

    for q in questions:
        QuestionBank.objects.create(
            round=q['round'],
            category=q['category'],
            question_text=q['text'],
            options=q['options'],
            correct_answer=q['correct'],
            attempt_count=q['attempts'],
            failure_count=q['fails'],
            moderation_status='APPROVED',
            submitted_by=admin_user
        )
    
    # Add one PENDING question
    QuestionBank.objects.create(
        round='ROUND_1_TECHNICAL',
        category='REACT',
        question_text='What is a React Hook?',
        options=['A function', 'A class', 'A style', 'A database'],
        correct_answer='A function',
        moderation_status='PENDING',
        submitted_by=admin_user
    )

    print("Governance Seed Data Complete.")

if __name__ == "__main__":
    seed_governance_data()
