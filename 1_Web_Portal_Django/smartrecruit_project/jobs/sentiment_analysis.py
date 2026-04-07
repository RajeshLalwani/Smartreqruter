"""
Interview Sentiment Analysis Engine — SmartRecruit
────────────────────────────────────────────────────────
Pure Python (no NLTK/spaCy required) sentiment analysis
on interview feedback text.

Analyzes:
  1. Overall Sentiment (Positive / Neutral / Negative)
  2. Tone Breakdown (Confidence, Clarity, Enthusiasm, Technical Depth)
  3. Keyword Extraction (positive/negative signals)
  4. Communication Score
  5. Recommended Action
"""

import os
import json
import re
from typing import Dict, List, Tuple
from django.conf import settings
from google import genai


# ─── Sentiment Lexicons ───────────────────────────────────────────

POSITIVE_SIGNALS = [
    # Strong positives
    'excellent', 'outstanding', 'exceptional', 'impressive', 'brilliant',
    'strong', 'great', 'good', 'well', 'solid', 'effective', 'clear',
    'confident', 'articulate', 'knowledgeable', 'experienced', 'thorough',
    'detailed', 'logical', 'structured', 'precise', 'accurate',
    # Technical positives
    'correct', 'right', 'accurate', 'demonstrated', 'showed', 'proved',
    'understood', 'grasped', 'explained well', 'answered correctly',
    'good understanding', 'strong fundamentals', 'deep knowledge',
    # Communication positives
    'communicated well', 'expressed clearly', 'good communication',
    'professional', 'enthusiastic', 'motivated', 'passionate',
    'team player', 'collaborative', 'proactive', 'quick learner',
]

NEGATIVE_SIGNALS = [
    # Weak performance
    'weak', 'poor', 'average', 'mediocre', 'below average', 'unsure',
    'uncertain', 'confused', 'struggled', 'difficulty', 'vague', 'unclear',
    'incorrect', 'wrong', 'missed', 'failed', 'lack', 'lacking',
    'limited', 'insufficient', 'inadequate', 'superficial', 'shallow',
    # Communication negatives
    'nervous', 'hesitant', 'incoherent', 'rambling', 'off-topic',
    'irrelevant', 'did not answer', 'avoided', 'evaded', 'fumbled',
    # Technical negatives
    'no understanding', 'could not explain', 'did not know', 'blank',
    'wrong approach', 'incorrect logic', 'fundamental error',
]

CONFIDENCE_WORDS = [
    'confident', 'assured', 'decisive', 'clear', 'direct', 'firm',
    'definitive', 'certain', 'sure', 'composed', 'calm',
]

HESITATION_WORDS = [
    'hesitant', 'uncertain', 'nervous', 'unsure', 'confused', 'struggled',
    'paused', 'blank', 'fumbled', 'unclear', 'undecided',
]

ENTHUSIASM_WORDS = [
    'enthusiastic', 'passionate', 'excited', 'motivated', 'eager',
    'interested', 'keen', 'proactive', 'driven', 'ambitious',
]

TECHNICAL_DEPTH_WORDS = [
    'algorithm', 'complexity', 'optimization', 'data structure', 'architecture',
    'design pattern', 'system design', 'performance', 'scalability',
    'deep knowledge', 'fundamentals', 'concept', 'mechanism', 'implementation',
    'explained', 'demonstrated', 'proved', 'correct approach',
]

NEGATORS = ['not', 'no', "doesn't", "didn't", "wasn't", "isn't", "cannot", "couldn't", "never", "hardly"]

# ─── Emoji Mapping ────────────────────────────────────────────────
SENTIMENT_ICONS = {
    'Very Positive': ('fas fa-smile-beam', 'success', '#00E676'),
    'Positive':      ('fas fa-smile',      'success', '#69F0AE'),
    'Neutral':       ('fas fa-meh',        'warning', '#FFD740'),
    'Negative':      ('fas fa-frown',      'danger',  '#FF5252'),
    'Very Negative': ('fas fa-tired',      'danger',  '#D50000'),
}


# ─── Core Analysis ────────────────────────────────────────────────

def analyze_interview_sentiment(feedback_text: str, interview_instance=None) -> Dict:
    """
    Elite Sentiment Analysis Engine using SmartRecruit Intelligence.
    Calculates Confidence, Clarity, Stress, and Honesty.
    """
    if not feedback_text or len(feedback_text.strip()) < 10:
        return _empty_result()

    api_key = os.environ.get("GEMINI_API_KEY")
    result = _empty_result()
    
    if api_key:
        try:
            client = genai.Client(api_key=api_key)
            prompt = f"""
            Perform a DEEP architectural and behavioral sentiment analysis on this interview response:
            "{feedback_text}"
            
            Evaluate exactly these dimensions (0-100):
            1. Confidence Score (based on directness and technical certainty)
            2. Clarity Score (based on structured logic and articulation)
            3. Stress Level (detect nervousness, hesitation, or 'fumbling' through text)
            4. Honesty Index (detect generic/template answers vs authentic unique experience)
            
            Return a JSON object:
            {{
                "sentiment_score": 0-100,
                "label": "Very Positive/Positive/Neutral/Negative",
                "dimensions": {{
                    "Confidence": 0-100,
                    "Clarity": 0-100,
                    "Stress": 0-100, 
                    "Honesty": 0-100
                }},
                "detailed_emotions": {{
                    "technical_enthusiasm": 0-1.0,
                    "anxiety": 0-1.0,
                    "professionalism": 0-1.0
                }},
                "rationale": "1-2 sentence peak professional insight",
                "key_phrases": ["list of most significant technical/behavioral terms"]
            }}
            """
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                config={'response_mime_type': 'application/json'},
                contents=prompt
            )
            data = json.loads(response.text)
            
            icon, color, hex_color = SENTIMENT_ICONS.get(data['label'], SENTIMENT_ICONS['Neutral'])
            
            result = {
                'overall_score': data['sentiment_score'],
                'overall_label': data['label'],
                'sentiment_icon': icon,
                'sentiment_color': color,
                'sentiment_hex': hex_color,
                'dimensions': data['dimensions'],
                'detailed_emotions': data['detailed_emotions'],
                'key_phrases': data['key_phrases'],
                'communication_score': round(sum(data['dimensions'].values()) / 4),
                'recommendation': {
                    'action': data['label'],
                    'action_color': color,
                    'rationale': data['rationale']
                },
                'word_count': len(feedback_text.split())
            }
            
            # Persist to database if instance provided
            if interview_instance:
                from .models import SentimentAnalysis
                SentimentAnalysis.objects.update_or_create(
                    interview=interview_instance,
                    defaults={
                        'confidence_score': data['dimensions'].get('Confidence', 0),
                        'clarity_score': data['dimensions'].get('Clarity', 0),
                        'stress_level': data['dimensions'].get('Stress', 0),
                        'honesty_index': data['dimensions'].get('Honesty', 0),
                        'detailed_emotions': data['detailed_emotions'],
                        'key_phrases': data['key_phrases']
                    }
                )
                
        except Exception as e:
            print(f"Elite Sentiment Error: {e}")
            
    return result


def _score_with_negation(text: str) -> Tuple[int, int]:
    """Tokenize and score positive/negative signals with basic negation detection."""
    words = text.split()
    pos = 0
    neg = 0
    for i, word in enumerate(words):
        # Check if preceded by a negator (within 3 words)
        negated = any(words[max(0, i-3):i].count(n) > 0 for n in NEGATORS)
        if word in POSITIVE_SIGNALS:
            if negated: neg += 1
            else:       pos += 1
        elif word in NEGATIVE_SIGNALS:
            if negated: pos += 1
            else:       neg += 1
    # Also check multi-word phrases
    for phrase in POSITIVE_SIGNALS:
        if ' ' in phrase and phrase in text:
            pos += 2
    for phrase in NEGATIVE_SIGNALS:
        if ' ' in phrase and phrase in text:
            neg += 2
    return pos, neg


def _dimension_score(text: str, positive: List[str], negative: List[str]) -> int:
    """Calculate a 0–100 dimension score."""
    p_count = sum(1 for w in positive if w in text)
    n_count = sum(1 for w in negative if w in text)
    raw = p_count - n_count
    return max(0, min(100, 50 + raw * 12))


def _extract_keywords(text: str, wordlist: List[str]) -> List[str]:
    """Extract which keywords from the list appear in text."""
    found = []
    for phrase in wordlist:
        if phrase in text:
            found.append(phrase)
    return list(dict.fromkeys(found))  # Preserve order, deduplicate


def _build_recommendation(label: str, score: float, neg_kws: List[str], pos_kws: List[str], ai_score: float) -> Dict:
    """Generate a structured recommendation based on analysis."""
    if label in ('Very Positive', 'Positive'):
        action = 'Advance to Next Round'
        action_color = 'success'
        rationale = (
            f"The candidate demonstrated strong performance with {len(pos_kws)} positive signals detected. "
            f"AI confidence at {ai_score:.0f}%. Recommended for advancement."
        )
    elif label == 'Neutral':
        action = 'Review Manually'
        action_color = 'warning'
        rationale = (
            f"Mixed performance signals detected. {len(pos_kws)} strengths and {len(neg_kws)} concerns noted. "
            "A human review of the full interview is recommended before deciding."
        )
    else:
        action = 'Reconsider / Reject'
        action_color = 'danger'
        issues = ', '.join(neg_kws[:3]) if neg_kws else 'multiple areas'
        rationale = (
            f"Interview performance raised concerns in: {issues}. "
            f"AI confidence at {ai_score:.0f}%. Consider not advancing this candidate."
        )
    return {
        'action':       action,
        'action_color': action_color,
        'rationale':    rationale,
    }


def _empty_result() -> Dict:
    return {
        'overall_score': 0,
        'overall_label': 'No Data',
        'sentiment_icon': 'fas fa-question-circle',
        'sentiment_color': 'secondary',
        'sentiment_hex': '#adb5bd',
        'dimensions': {'Confidence': 0, 'Enthusiasm': 0, 'Technical Depth': 0, 'Clarity': 0},
        'positive_keywords': [],
        'negative_keywords': [],
        'communication_score': 0,
        'recommendation': {
            'action': 'Insufficient Data',
            'action_color': 'secondary',
            'rationale': 'No interview feedback text available for analysis.',
        },
        'word_count': 0,
    }


# ─── Batch Analysis ───────────────────────────────────────────────

def analyze_all_interviews(application) -> Dict:
    """
    Run sentiment analysis on all completed interviews for an application.
    Returns per-round analysis and aggregate.
    """
    from .models import Interview
    results = {}
    interviews = Interview.objects.filter(
        application=application, status='COMPLETED'
    ).exclude(feedback='')

    for iv in interviews:
        results[iv.get_interview_type_display()] = analyze_interview_sentiment(
            iv.feedback, iv
        )

    return results
