import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartrecruit_project.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()
users = [(u.username, u.is_superuser, u.is_staff) for u in User.objects.all()]
print(f"Users: {users}")
