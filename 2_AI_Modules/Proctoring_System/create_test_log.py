import os
import sys
import django
from pathlib import Path
from django.core.files import File

# Setup Django
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent / "1_Web_Portal_Django" / "smartrecruit_project"
sys.path.append(str(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartrecruit_project.settings')
django.setup()

from jobs.models import ProctoringLog, Application
from django.contrib.auth import get_user_model

User = get_user_model()

def create_test_log():
    # Ensure at least one application exists (or create dummy)
    # For now, let's try to find one
    app = Application.objects.first()
    if not app:
        print("No application found. Cannot create log.")
        return

    # Create a log with the test image
    log = ProctoringLog(
        application=app,
        log_type='SCREENSHOT',
        details='Manual Test Log'
    )
    
    # Open the test image
    with open('test_image.jpg', 'rb') as f:
        log.image.save('test_image.jpg', File(f), save=True)
        
    print(f"Created Test Log ID: {log.id}")

if __name__ == "__main__":
    create_test_log()
