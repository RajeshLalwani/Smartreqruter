import json
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from jobs.models import Application, PredictiveInsight

def build_feature_vector(application):
    """
    Constructs a feature vector for the given candidate application.
    Features:
    0 - Technical IQ
    1 - Communication
    2 - Confidence
    3 - Integrity 
    4 - Problem Solving
    """
    technical = float(application.technical_score) if application.technical_score else 0.0
    communication = float(application.communication_score) if application.communication_score else 0.0
    confidence = float(application.confidence_score) if application.confidence_score else 0.0
    integrity = float(application.integrity_score) if application.integrity_score else 0.0
    problem_solving = float(application.problem_solving_score) if application.problem_solving_score else 0.0
    
    return np.array([technical, communication, confidence, integrity, problem_solving])

def get_top_performer_benchmark():
    """Returns the ideal top performer baseline scores"""
    return {
        'Technical': 95.0,
        'Communication': 90.0,
        'Confidence': 88.0,
        'Integrity': 100.0,
        'Problem Solving': 92.0
    }

def generate_success_probability(application_id):
    """
    Trains a lightweight Random Forest model, calculates the candidate's success probability,
    and saves the result to PredictiveInsight.
    """
    try:
        app = Application.objects.get(id=application_id)
        
        # 1. Mock Training Data (In real world, fetch from historical database)
        # Features: [Tech, Comm, Conf, Integ, Prob]
        X_train = np.array([
            [95, 90, 88, 100, 92],  # Top Hire
            [85, 80, 85, 100, 80],  # Good Hire
            [70, 75, 60, 100, 65],  # Average
            [50, 40, 50, 80, 45],   # Poor Fit
            [20, 30, 40, 100, 20],  # Very Poor
            [90, 85, 80, 0, 85],    # High Tech, Zero Integrity (Immediate reject)
            [88, 85, 80, 50, 85],   # High Tech, Low Integrity
            [95, 95, 95, 100, 95]   # Exceptional
        ])
        y_train = np.array([1, 1, 0, 0, 0, 0, 0, 1]) # 1 = Success, 0 = Failure
        
        # 2. Train Model
        clf = RandomForestClassifier(n_estimators=50, random_state=42, max_depth=5)
        clf.fit(X_train, y_train)
        
        # 3. Extract Candidate Features
        candidate_features = build_feature_vector(app)
        X_test = candidate_features.reshape(1, -1)
        
        # 4. Predict success probability
        # predict_proba returns [[P(class_0), P(class_1)]]
        prob_success = clf.predict_proba(X_test)[0][1] * 100
        
        # 5. Extract Feature Importance
        importances = clf.feature_importances_
        feature_names = ['Technical', 'Communication', 'Confidence', 'Integrity', 'Problem Solving']
        
        feature_importance_map = {}
        for name, imp in zip(feature_names, importances):
            feature_importance_map[name] = round(imp * 100, 2)
            
        # 6. Gap Analysis against Top Performer
        benchmark = get_top_performer_benchmark()
        gap_analysis = {
            'candidate_scores': {
                'Technical': candidate_features[0],
                'Communication': candidate_features[1],
                'Confidence': candidate_features[2],
                'Integrity': candidate_features[3],
                'Problem Solving': candidate_features[4]
            },
            'benchmark_scores': benchmark,
            'gaps': {
                'Technical': max(0.0, benchmark['Technical'] - candidate_features[0]),
                'Communication': max(0.0, benchmark['Communication'] - candidate_features[1]),
                'Confidence': max(0.0, benchmark['Confidence'] - candidate_features[2]),
                'Integrity': max(0.0, benchmark['Integrity'] - candidate_features[3]),
                'Problem Solving': max(0.0, benchmark['Problem Solving'] - candidate_features[4])
            }
        }
        
        # 7. Save to Database
        insight, created = PredictiveInsight.objects.update_or_create(
            application=app,
            defaults={
                'success_probability': round(prob_success, 1),
                'feature_importance_json': feature_importance_map,
                'gap_analysis_json': gap_analysis
            }
        )
        
        return insight
        
    except Exception as e:
        print(f"ML Pipeline Error: {e}")
        return None
