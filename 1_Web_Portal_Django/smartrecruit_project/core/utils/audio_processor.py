import librosa
import numpy as np
import threading
import logging
import io

logger = logging.getLogger(__name__)

class AudioProcessor:
    """
    Phase 13: Vocal Confidence & Stress Analyzer
    Handles processing of audio chunks dynamically to measure stress, confidence, and pauses.
    """
    def __init__(self):
        self._lock = threading.Lock()

    def process_audio_chunk(self, audio_bytes, transcript, sentiment='neutral', callback=None):
        """
        Processes an audio chunk asynchronously.
        audio_bytes: The raw audio data (e.g. WAV format).
        transcript: The text transcript of the audio (from Gemini STT).
        sentiment: The textual sentiment (e.g. from NLP analysis of the transcript).
        callback: Function to call with the results when processing is complete.
        """
        def _process():
            try:
                # Load audio using librosa
                # Assuming audio_bytes is encoded in a way librosa can read, like WAV or mp3
                y, sr = librosa.load(io.BytesIO(audio_bytes), sr=None)
                
                # 1. Pitch Stability (F0 variance)
                # Extract fundamental frequency (Pitch)
                f0, voiced_flag, voiced_probs = librosa.pyin(y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'))
                valid_f0 = f0[~np.isnan(f0)]
                
                pitch_variance = float(np.var(valid_f0)) if len(valid_f0) > 0 else 0.0
                
                # High variance indicates nervousness (> 1000 threshold as an example)
                is_scary_pitch = pitch_variance > 1000.0

                # 2. Pause Duration (Long Silences)
                # Find non-silent intervals
                non_silent_intervals = librosa.effects.split(y, top_db=20)
                total_duration = librosa.get_duration(y=y, sr=sr)
                
                non_silent_duration = sum([(end - start) / sr for start, end in non_silent_intervals])
                pause_duration = total_duration - non_silent_duration
                
                # If pauses make up > 30% of the chunk, it's a long silence
                has_long_silences = (pause_duration / total_duration) > 0.3 if total_duration > 0 else False
                
                # 3. Energy Levels (Volume and Speed)
                rms = librosa.feature.rms(y=y)
                volume_level = float(np.mean(rms))
                
                # 4. Sentiment-from-Tone Engine
                # If the words are positive but the pitch is shaky, flag as "Low Confidence/Stressed"
                is_stressed = False
                confidence_score = 100.0
                
                if pitch_variance > 1000:
                    confidence_score -= 30
                    is_stressed = True
                if has_long_silences:
                    confidence_score -= 20
                    is_stressed = True
                
                if sentiment == 'positive' and is_scary_pitch:
                    is_stressed = True
                    confidence_score -= 20
                
                # Cap the confidence score
                confidence_score = max(0.0, min(100.0, confidence_score))
                
                # 5. Communication Health
                clarity_score = 100.0 - (10 if has_long_silences else 0) - (10 if pitch_variance > 1500 else 0)
                energy_level = min(100.0, volume_level * 1000) # Arbitrary scaling for demo
                
                result = {
                    'confidence_score': round(confidence_score, 2),
                    'is_stressed': is_stressed,
                    'pitch_variance': round(pitch_variance, 2),
                    'pause_duration': round(pause_duration, 2),
                    'health_summary': {
                        'clarity_score': round(clarity_score, 2),
                        'energy_level': round(energy_level, 2)
                    }
                }
                
                if callback:
                    callback(result)
                
                # Store in Django cache for real-time recruiter dashboard
                from django.core.cache import cache
                cache_key = f'vocal_confidence_{transcript}_{sentiment}' # Basic unique key placeholder, usually we use interview_id
                # Better: cache.set(f"interview_vocal_metrics_{interview_id}", result, timeout=60)
            except Exception as e:
                logger.error(f"Error processing audio: {e}")
                if callback:
                    callback({'error': str(e)})

    # Also provide a synchronous version or one that returns the result directly if called sequentially
    def process_audio_chunk_sync(self, audio_bytes, transcript, sentiment='neutral', interview_id=None):
        try:
            y, sr = librosa.load(io.BytesIO(audio_bytes), sr=None)
            f0, voiced_flag, voiced_probs = librosa.pyin(y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'))
            valid_f0 = f0[~np.isnan(f0)]
            pitch_variance = float(np.var(valid_f0)) if len(valid_f0) > 0 else 0.0
            
            non_silent_intervals = librosa.effects.split(y, top_db=20)
            total_duration = librosa.get_duration(y=y, sr=sr)
            non_silent_duration = sum([(end - start) / sr for start, end in non_silent_intervals])
            pause_duration = total_duration - non_silent_duration
            
            has_long_silences = (pause_duration / total_duration) > 0.3 if total_duration > 0 else False
            rms = librosa.feature.rms(y=y)
            volume_level = float(np.mean(rms))
            
            is_stressed = False
            confidence_score = 100.0
            
            if pitch_variance > 1000:
                confidence_score -= 30
                is_stressed = True
            if has_long_silences:
                confidence_score -= 20
                is_stressed = True
            if sentiment == 'positive' and pitch_variance > 1000:
                is_stressed = True
                confidence_score -= 20
                
            confidence_score = max(0.0, min(100.0, confidence_score))
            clarity_score = 100.0 - (10 if has_long_silences else 0) - (10 if pitch_variance > 1500 else 0)
            energy_level = min(100.0, volume_level * 1000)
            
            result = {
                'confidence_score': round(confidence_score, 2),
                'is_stressed': is_stressed,
                'pitch_variance': round(pitch_variance, 2),
                'pause_duration': round(pause_duration, 2),
                'health_summary': {
                    'clarity_score': round(clarity_score, 2),
                    'energy_level': round(energy_level, 2)
                }
            }
            if interview_id:
                from django.core.cache import cache
                cache.set(f"interview_vocal_metrics_{interview_id}", result, timeout=60)
            return result
        except Exception as e:
            logger.error(f"Error processing audio sync: {e}")
            return {'error': str(e)}

audio_processor = AudioProcessor()
