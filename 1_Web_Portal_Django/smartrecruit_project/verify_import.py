import os
import django
import csv
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartrecruit_project.settings')
django.setup()

from jobs.models import QuestionBank
from django.contrib.auth import get_user_model
User = get_user_model()
admin_user = User.objects.filter(is_superuser=True).first()

def test_import():
    csv_path = 'test_questions.csv'
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            try:
                # Fix single quotes in JSON strings
                raw_options = row.get('options', '[]').replace("'", '"')
                options_list = json.loads(raw_options) if raw_options else []
                
                QuestionBank.objects.create(
                    round=row['round'],
                    category=row.get('category', 'LOGICAL'),
                    difficulty=row.get('difficulty', 'medium'),
                    question_text=row['question_text'],
                    options=options_list,
                    correct_answer=row['correct_answer'],
                    explanation=row.get('explanation', ''),
                    is_coding=row.get('is_coding', 'False').lower() == 'true',
                    moderation_status='APPROVED',
                    submitted_by=admin_user
                )
                count += 1
            except Exception as e:
                print(f"Error importing row: {e}")
        print(f"Successfully imported {count} questions.")

if __name__ == "__main__":
    test_import()
