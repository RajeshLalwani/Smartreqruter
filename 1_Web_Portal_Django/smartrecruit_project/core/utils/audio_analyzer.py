import librosa
import numpy as np
import io
import wave

class AudioAnalyzer:
    def __init__(self, sample_rate=22050):
        self.sample_rate = sample_rate

    def analyze_stress(self, audio_bytes):
        """
        Analyzes audio bytes for stress markers: Pitch Variance, Jitter, and Shimmer.
        """
        try:
            # Load audio from bytes
            y, sr = librosa.load(io.BytesIO(audio_bytes), sr=self.sample_rate)
            
            if len(y) == 0:
                return {"error": "Empty Audio"}

            # 1. Pitch Variance
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
            pitch_values = pitches[pitches > 0]
            pitch_variance = np.var(pitch_values) if len(pitch_values) > 0 else 0
            
            # 2. Jitter (Micro-tremors in pitch)
            # Simplified: frequency oscillation
            jitter = np.mean(np.abs(np.diff(pitch_values))) / np.mean(pitch_values) if len(pitch_values) > 1 else 0

            # 3. Shimmer (Amplitude variation)
            rms = librosa.feature.rms(y=y)[0]
            shimmer = np.mean(np.abs(np.diff(rms))) / np.mean(rms) if np.mean(rms) > 0 else 0

            # 4. Stress Index Calculation (Heuristic)
            # High jitter + low pitch variance (flat/monotone stress) = high stress
            stress_index = (jitter * 500) + (shimmer * 200)
            if pitch_variance < 1000: stress_index += 20 # Flat voice indicator
            
            stress_index = min(100, max(0, stress_index))

            return {
                "stress_index": round(stress_index, 2),
                "pitch_variance": round(float(pitch_variance), 2),
                "jitter": round(float(jitter), 4),
                "shimmer": round(float(shimmer), 4),
                "confidence_score": round(100 - stress_index, 2)
            }

        except Exception as e:
            return {"error": str(e)}

    def estimate_wpm(self, audio_bytes, word_count):
        """
        Estimates Words Per Minute based on audio duration and provided word count.
        """
        try:
            y, sr = librosa.load(io.BytesIO(audio_bytes), sr=self.sample_rate)
            duration_sec = librosa.get_duration(y=y, sr=sr)
            
            if duration_sec == 0: return 0
            
            wpm = (word_count / duration_sec) * 60
            return round(wpm, 1)
        except:
            return 0
