import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartrecruit_project.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

print(f"{'Username':<20} | {'Email':<25} | {'Superuser':<10} | {'Staff':<10} | {'Recruiter':<10}")
print("-" * 85)

for u in User.objects.all():
    is_recruiter = getattr(u, 'is_recruiter', 'N/A')
    print(f"{u.username:<20} | {u.email:<25} | {str(u.is_superuser):<10} | {str(u.is_staff):<10} | {str(is_recruiter):<10}")
