import json
import numpy as np
from django.utils import timezone
from sklearn.ensemble import RandomForestRegressor
from jobs.models import Assessment, SentimentLog, TurnoverPrediction, Application

class RetentionAnalyticsEngine:
    """
    ML-Driven Engine to estimate potential employee turnover based on multi-modal telemetry.
    """
    
    # Weightage for different survival factors
    WEIGHTS = {
        'technical_consistency': 0.30,  # Performance stability across rounds
        'sentiment_stability': 0.20,      # Emotional regulation during high-stress rounds
        'engagement_level': 0.20,         # Speed vs. quality of responses
        'experience_gap': 0.20,           # Claimed vs. actual technical depth
        'behavioral_alignment': 0.10      # Culture fit score
    }

    @staticmethod
    def calculate_technical_consistency(application):
        """Calculates variance in scores across different rounds."""
        assessments = Assessment.objects.filter(application=application)
        if not assessments.exists():
            return 70.0
        scores = [a.score for a in assessments]
        if len(scores) < 2:
            return scores[0] if scores else 70.0
        
        # Stability = 100 - (Std Dev normalized to 0-40 range)
        std_dev = np.std(scores)
        consistency = max(0, 100 - (std_dev * 2.5)) 
        return consistency

    @staticmethod
    def calculate_sentiment_stability(application):
        """Analyzes frequency of Neutral/Confident vs Stressed states."""
        interviews = application.interviews.all()
        logs = SentimentLog.objects.filter(interview__in=interviews)
        
        if not logs.exists():
            return 75.0
        
        emotions = [log.emotion for log in logs]
        total = len(emotions)
        # Neutral + Happy (Confident) are stable indicators
        stable_count = emotions.count('neutral') + emotions.count('happy')
        # Fearful + Angry are "Stressed" indicators
        stressed_count = emotions.count('fearful') + emotions.count('angry')
        
        stability = (stable_count / total) * 100 if total > 0 else 75.0
        # Penalty for high stress
        if total > 0 and (stressed_count / total) > 0.3:
            stability *= 0.8
            
        return min(100, stability)

    @staticmethod
    def calculate_engagement_level(application):
        """Measures total time spent vs quality of responses (MOCKED)."""
        assessments = Assessment.objects.filter(application=application)
        if not assessments.exists():
            return 80.0
        
        # Quality = Score / Time
        engagement_scores = []
        for a in assessments:
            if a.time_taken and a.time_taken.total_seconds() > 0:
                quality_ratio = a.score / (a.time_taken.total_seconds() / 60) # Score per minute
                engagement_scores.append(quality_ratio)
        
        if not engagement_scores:
            return 80.0
            
        avg_eng = np.mean(engagement_scores)
        # Normalize: Assume 10 points/min is elite engagement (100%)
        return min(100, (avg_eng / 5) * 100)

    @staticmethod
    def calculate_experience_gap(candidate, application):
        """Compares claimed experience vs actual technical depth from AI score."""
        claimed = candidate.experience_years or 0
        actual_score = application.ai_score or 0
        
        # Heuristic: If they claim 10 years but score < 50, Gap is high.
        # Expectation: 10 points per year of experience
        expected_score = min(100, claimed * 10)
        gap = abs(expected_score - actual_score)
        
        # Fidelity = 100 - Gap
        experience_fidelity = max(0, 100 - gap)
        return experience_fidelity

    @classmethod
    def run_prediction(cls, candidate):
        """
        Executes the AI Predictive Model to forecast retention.
        """
        application = Application.objects.filter(candidate=candidate).order_by('-applied_at').first()
        if not application:
            return None

        # 1. Aggregate Stability Indicators
        tech_cons = cls.calculate_technical_consistency(application)
        sent_stab = cls.calculate_sentiment_stability(application)
        eng_level = cls.calculate_engagement_level(application)
        exp_gap = cls.calculate_experience_gap(candidate, application)
        behavioral = 85.0 if application.ai_score > 80 else 65.0 # Logic-based fallback

        # 2. Predictive Model Simulation (Random Forest logic)
        # In a production environment, this would load a joblib/pickle model.
        # Here we use a weighted regressor for deterministic real-time output.
        X = np.array([[tech_cons, sent_stab, eng_level, exp_gap, behavioral]])
        weights = np.array([cls.WEIGHTS[k] for k in ['technical_consistency', 'sentiment_stability', 'engagement_level', 'experience_gap', 'behavioral_alignment']])
        
        retention_score = np.dot(X, weights)[0]

        # 3. Generate Radar Data for Chart.js
        radar_data = {
            "labels": ["Technical", "Sentiment", "Engagement", "Experience", "Alignment"],
            "datasets": [
                {
                    "label": "Candidate Profile",
                    "data": [tech_cons, sent_stab, eng_level, exp_gap, behavioral],
                    "borderColor": "#00d2ff",
                    "backgroundColor": "rgba(0, 210, 255, 0.1)",
                    "pointBackgroundColor": "#00d2ff",
                    "borderWidth": 2
                },
                {
                    "label": "Stability Benchmark",
                    "data": [90, 85, 80, 85, 90],
                    "borderColor": "rgba(255, 255, 255, 0.2)",
                    "borderDash": [5, 5],
                    "backgroundColor": "transparent",
                    "pointRadius": 0
                }
            ]
        }

        # 4. Persistence
        prediction, created = TurnoverPrediction.objects.update_or_create(
            candidate=candidate,
            defaults={
                'retention_score': round(retention_score, 2),
                'technical_stability': round(tech_cons, 2),
                'sentiment_stability': round(sent_stab, 2),
                'behavioral_alignment': round(behavioral, 2),
                'time_efficiency': round(eng_level, 2),
                'radar_data': radar_data
            }
        )
        
        return prediction
