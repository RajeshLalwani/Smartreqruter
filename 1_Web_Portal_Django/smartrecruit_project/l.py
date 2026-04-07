import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartrecruit_project.settings')
django.setup()
from django.contrib.auth import get_user_model
for u in get_user_model().objects.all():
    print(f"User: {u.username} Super: {u.is_superuser} Staff: {u.is_staff}")
