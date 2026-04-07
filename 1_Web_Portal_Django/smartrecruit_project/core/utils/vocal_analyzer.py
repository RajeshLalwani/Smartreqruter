import time
import logging

logger = logging.getLogger(__name__)

class VocalAnalyzer:
    """
    Analyzes vocal patterns from transcripts to determine confidence and engagement.
    """
    
    @staticmethod
    def calculate_metrics(transcript, duration_seconds):
        """
        Calculates speech rate and basic pause density.
        """
        if not transcript or duration_seconds <= 0:
            return {'wpm': 0, 'pause_density': 0, 'confidence_impact': 0}
            
        words = transcript.strip().split()
        word_count = len(words)
        
        # 1. Speech Rate (Words Per Minute)
        # Avg conversational speed is 120-150 WPM.
        wpm = (word_count / duration_seconds) * 60
        
        # 2. Pause Density (Higher if few words over long time)
        # Heuristic: 1 word per 2 seconds is very slow/hesitant.
        pause_density = max(0, 1.0 - (word_count / (duration_seconds / 2.0)))
        
        # 3. Confidence Heuristic
        # Low WPM (< 80) or High Pause Density (> 0.6) reduces confidence.
        confidence_impact = 0
        if wpm < 80: confidence_impact -= 10
        if pause_density > 0.6: confidence_impact -= 15
        if 110 < wpm < 160: confidence_impact += 10 # Optimal range
        
        return {
            'wpm': round(wpm, 2),
            'pause_density': round(pause_density, 2),
            'confidence_impact': confidence_impact
        }

    @staticmethod
    def get_behavioral_summary(transcript, metrics):
        """
        Quick procedural summary before deep AI analysis.
        """
        if metrics['wpm'] > 180:
            return "Fast-paced/Anxious delivery."
        elif metrics['wpm'] < 70:
            return "Highly hesitant or deeply reflective delivery."
        return "Steady, conversational delivery."
