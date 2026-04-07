import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartrecruit_project.settings')
django.setup()

from jobs.models import PlatformSetting

def init_proctor_settings():
    PlatformSetting.set('PROCTOR_MIN_CONFIDENCE', '0.5', 'Minimum Face Detection Confidence', 'proctoring')
    PlatformSetting.set('PROCTOR_EYE_RATIO_LOW', '0.35', 'Eye Gaze Low Threshold (Wandering)', 'proctoring')
    PlatformSetting.set('PROCTOR_EYE_RATIO_HIGH', '0.65', 'Eye Gaze High Threshold (Wandering)', 'proctoring')
    PlatformSetting.set('PROCTOR_FLAGS_MAX', '5', 'Max flags before session is auto-flagged for review', 'proctoring')
    print("Proctoring settings initialized.")

if __name__ == "__main__":
    init_proctor_settings()
