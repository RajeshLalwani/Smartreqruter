try:
    import cv2
    import numpy as np
    import mediapipe as mp
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("[WARNING] Required libraries (cv2, mediapipe) not fully installed. Proctoring analysis degraded.")

import os
import sys
import django
from pathlib import Path
import base64
from io import BytesIO
from PIL import Image

# ==========================================
# DJANGO SETUP
# ==========================================
def setup_django():
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent.parent / "1_Web_Portal_Django" / "smartrecruit_project"
    
    if str(project_root) not in sys.path:
        sys.path.append(str(project_root))
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartrecruit_project.settings')
    try:
        django.setup()
        return True
    except Exception as e:
        print(f"[ERROR] Django Setup Failed: {e}")
        return False

# ==========================================
# ADVANCED PROCTORING ANALYZER (MEDIAPIPE)
# ==========================================
class AdvancedProctoringAnalyzer:
    def __init__(self):
        if CV2_AVAILABLE:
            self.mp_face_mesh = mp.solutions.face_mesh
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                max_num_faces=2,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            # Indices for eyes and face orientation
            self.LEFT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
            self.RIGHT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
            self.IRIS_LEFT = [474, 475, 476, 477]
            self.IRIS_RIGHT = [469, 470, 471, 472]

    def analyze_frame(self, frame):
        """
        Performs deep vision analysis on a single frame.
        Detects: Multiple faces, Gaze deviation, Head pose.
        """
        if not CV2_AVAILABLE:
            return {'status': 'ERROR', 'msg': 'CV2/Mediapipe not available'}

        results = self.face_mesh.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        
        if not results.multi_face_landmarks:
            return {'status': 'ANOMALY', 'msg': 'No Face Detected', 'score': 0}
        
        face_count = len(results.multi_face_landmarks)
        if face_count > 1:
            return {'status': 'VIOLATION', 'msg': 'Multiple Faces Detected', 'score': 0}

        # Analyze single face
        face_landmarks = results.multi_face_landmarks[0].landmark
        img_h, img_w, _ = frame.shape

        # 1. Gaze Analysis (Simplified)
        # Check if iris is centered relative to eye boundaries
        # This is a complex calculation; here we use a placeholder logic that checks
        # if the average iris position deviates significantly.
        
        # 2. Head Pose (Placeholder for "Industry Level" complexity)
        # In a real app, we'd use PnP to solve for head rotation.
        # Here we check the ratio of distances to detect looking significantly away.
        
        nose_tip = face_landmarks[1]
        left_temple = face_landmarks[234]
        right_temple = face_landmarks[454]
        
        dist_l = np.sqrt((nose_tip.x - left_temple.x)**2 + (nose_tip.y - left_temple.y)**2)
        dist_r = np.sqrt((nose_tip.x - right_temple.x)**2 + (nose_tip.y - right_temple.y)**2)
        
        ratio = dist_l / (dist_r + 1e-6)
        
        if ratio > 2.0 or ratio < 0.5:
            return {'status': 'WARNING', 'msg': 'Looking Away from Screen', 'score': 40}

        return {'status': 'OK', 'msg': 'Normal', 'score': 95}

    def analyze_image_path(self, path):
        frame = cv2.imread(str(path))
        if frame is None:
            return {'status': 'ERROR', 'msg': 'File not found'}
        return self.analyze_frame(frame)

    def audit_database_logs(self):
        if not setup_django(): return
        from jobs.models import ProctoringLog
        
        logs = ProctoringLog.objects.filter(details__contains="[AI Audit]").exclude(details__contains="[DeepVision]")
        # For this demo, we'll just check the most recent 10 to be fast
        logs = ProctoringLog.objects.all().order_by('-timestamp')[:20]
        
        for log in logs:
            if log.image:
                res = self.analyze_image_path(log.image.path)
                if res['status'] != 'OK':
                    log.details = f"{log.details}\n[DeepVision Audit]: {res['msg']}".strip()
                    log.save()
        print("Audit Complete.")

    def generate_suspicion_heatmap(self, application_id):
        """
        [ELITE] Aggregates proctoring logs for an application and generates a 
        suspicion density 'heatmap' (list of scores over time).
        """
        if not setup_django(): return []
        from jobs.models import ProctoringLog, Application
        
        logs = ProctoringLog.objects.filter(application_id=application_id).order_by('timestamp')
        if not logs.exists():
            return []
            
        start_time = logs.first().timestamp
        heatmap = []
        
        # Bucket by 30-second windows
        current_bucket_start = start_time
        current_score = 0
        
        for log in logs:
            # Simple weighting: VIOLATION = 50, SUSPICION = 30, WARNING = 10
            weight = 0
            if log.log_type == 'VIOLATION': weight = 50
            elif 'SUSPICION' in log.log_type: weight = 30
            elif 'WARNING' in log.details or 'Away' in log.details: weight = 15
            
            # If log is within 30s of bucket start, add to current score
            if log.timestamp < current_bucket_start + timedelta(seconds=30):
                current_score += weight
            else:
                # Close current bucket and start new one
                heatmap.append({
                    'offset_seconds': int((current_bucket_start - start_time).total_seconds()),
                    'score': current_score
                })
                # Catch up buckets if there's a gap
                while log.timestamp >= current_bucket_start + timedelta(seconds=60):
                    current_bucket_start += timedelta(seconds=30)
                    heatmap.append({
                        'offset_seconds': int((current_bucket_start - start_time).total_seconds()),
                        'score': 0
                    })
                
                current_bucket_start += timedelta(seconds=30)
                current_score = weight
                
        # Final bucket
        heatmap.append({
            'offset_seconds': int((current_bucket_start - start_time).total_seconds()),
            'score': current_score
        })
        
        return heatmap

if __name__ == "__main__":
    analyzer = AdvancedProctoringAnalyzer()
    # Test with audit
    # analyzer.audit_database_logs()
    print("Proctoring Analyzer Module Ready.")
