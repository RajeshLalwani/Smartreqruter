import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartrecruit_project.settings')
django.setup()

from jobs.models import PlatformSetting
val = PlatformSetting.get('ACTIVE_LLM')
print(f"ACTIVE_LLM is now: {val}")
