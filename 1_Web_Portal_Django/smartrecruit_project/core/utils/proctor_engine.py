import cv2
import mediapipe as mp
import numpy as np
import base64
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class ProctorEngine:
    _face_detector: Any = None
    _face_mesh: Any = None

    def __init__(self) -> None:
        from jobs.models import PlatformSetting
        self.mp_face_detection = mp.solutions.face_detection
        self.mp_face_mesh = mp.solutions.face_mesh
        
        # Fetch dynamic settings
        min_conf = float(PlatformSetting.get('PROCTOR_MIN_CONFIDENCE', '0.5'))
        self.eye_low = float(PlatformSetting.get('PROCTOR_EYE_RATIO_LOW', '0.35'))
        self.eye_high = float(PlatformSetting.get('PROCTOR_EYE_RATIO_HIGH', '0.65'))

        # Singleton pattern for heavy models (Upgraded max_faces for Sentinel)
        if ProctorEngine._face_detector is None:
            ProctorEngine._face_detector = self.mp_face_detection.FaceDetection(
                model_selection=0, min_detection_confidence=min_conf
            )
        if ProctorEngine._face_mesh is None:
            ProctorEngine._face_mesh = self.mp_face_mesh.FaceMesh(
                max_num_faces=5, # Sentinel scans up to 5 faces
                refine_landmarks=True, 
                min_detection_confidence=min_conf
            )
        
        self.face_detector = ProctorEngine._face_detector
        self.face_mesh = ProctorEngine._face_mesh

    def decode_base64_image(self, base64_string: str) -> Any:
        """Converts base64 string to a cv2 image."""
        try:
            if not base64_string: return None
            if ',' in base64_string:
                base64_string = base64_string.split(',')[1]
            img_data = base64.b64decode(base64_string)
            np_arr = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            return img
        except Exception as e:
            logger.error(f"Error decoding base64 image: {e}")
            return None

    def analyze_frame(self, frame_b64: str) -> dict:
        """
        SENTINEL CORE: Analyzes frame for cheating indicators.
        Returns: {face_count, attention_score, eye_gaze, stress_estimate, violations}
        """
        img = self.decode_base64_image(frame_b64)
        if img is None:
            return {"error": "Invalid Image"}

        h, w, _ = img.shape
        # Initialize with explicit types to satisfy linter
        results: dict = {
            "face_count": 0,
            "attention_score": 100,
            "eye_gaze": "FOCUSED",
            "stress_estimate": 0,
            "violations": []
        }

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # 1. Multi-face Detection
        if self.face_detector:
            face_results = self.face_detector.process(img_rgb)
            if face_results and face_results.detections:
                results["face_count"] = len(face_results.detections)
                if results["face_count"] > 1:
                    results["violations"].append("MULTIPLE_FACES_DETECTED")
                    results["attention_score"] -= 50
            else:
                results["violations"].append("PEOPLE_ABSENT")
                results["attention_score"] = 0

        # 2. Advanced Head Pose & Gaze (Mesh)
        if self.face_mesh:
            mesh_results = self.face_mesh.process(img_rgb)
            if mesh_results and mesh_results.multi_face_landmarks:
                landmarks = mesh_results.multi_face_landmarks[0].landmark
                
                # Gaze Estimation Logic
                left_iris = landmarks[468] 
                left_inner = landmarks[133]
                left_outer = landmarks[33]
                
                dist_total = left_inner.x - left_outer.x
                if dist_total != 0:
                    ratio = (left_iris.x - left_outer.x) / dist_total
                    if ratio < self.eye_low or ratio > self.eye_high:
                        results["eye_gaze"] = "WANDERING"
                        results["violations"].append("WANDERING_EYE_GAZE")
                        results["attention_score"] -= 30
                
                # Head Pose Placeholder (Simplified Y-axis check)
                nose = landmarks[1]
                if nose.x < 0.4 or nose.x > 0.6: # Turning head significantly
                    results["violations"].append("SUSPICIOUS_HEAD_ORIENTATION")
                    results["attention_score"] -= 20

        # Normalize attention
        results["attention_score"] = max(0, results["attention_score"])
        
        return results
