import re
import statistics

class VoiceAnalytics:
    @staticmethod
    def analyze_voice_metadata(transcript, duration_seconds, volume_data=None):
        """
        Calculates vocal confidence and speech metrics.
        
        :param transcript: Processed text from STT
        :param duration_seconds: Total speaking time
        :param volume_data: List of volume levels (0.0 to 1.0) sampled during speech
        :return: dict with scores and metrics
        """
        if not transcript or duration_seconds <= 0:
            return {
                "vocal_confidence_score": 0.0,
                "speech_rate": 0.0,
                "hesitation_count": 0,
                "volume_consistency": 0.0
            }

        words = transcript.split()
        word_count = len(words)
        
        # 1. Speech Rate (Words Per Minute)
        # Ideally 120-150 WPM for normal professional speech
        wpm = (word_count / duration_seconds) * 60
        
        # 2. Hesitation Patterns
        # Common filler words and pauses
        fillers = ['um', 'uh', 'ah', 'like', 'you know', 'err']
        hesitation_count = 0
        for word in words:
            if word.lower().strip(',.?!') in fillers:
                hesitation_count += 1
        
        # Additional points for punctuation/pauses if transcript includes '...'
        hesitation_count += transcript.count('...')

        # 3. Volume Consistency
        volume_consistency = 1.0
        if volume_data and len(volume_data) > 0:
            if len(volume_data) > 1:
                try:
                    std_dev = statistics.stdev(volume_data)
                    # Higher std_dev means less consistency. 
                    # We normalize this: 0.0 (erratic) to 1.0 (perfectly stable)
                    volume_consistency = max(0.0, 1.0 - (std_dev * 2))
                except Exception:
                    volume_consistency = 1.0
            else:
                volume_consistency = 1.0

        # 4. Final Confidence Score Calculation
        # Factors: Speech rate (optimum range), Low hesitation, High volume consistency
        
        # Rate Score: Peak at 140 WPM, drops if too fast or too slow
        rate_score = max(0.0, 100.0 - abs(wpm - 140) * 0.5)
        
        # Hesitation Penalty: -5 per hesitation, capped at 40
        hesitation_penalty = min(40.0, float(hesitation_count) * 5.0)
        
        # Consistency Score
        consistency_score = volume_consistency * 100
        
        confidence_score = (rate_score * 0.4) + (consistency_score * 0.4) + ((100.0 - hesitation_penalty) * 0.2)
        confidence_score = round(float(min(100.0, max(0.0, float(confidence_score)))), 1)

        return {
            "vocal_confidence_score": confidence_score,
            "speech_rate": round(float(wpm), 1),
            "hesitation_count": hesitation_count,
            "volume_consistency": round(float(volume_consistency), 2)
        }
