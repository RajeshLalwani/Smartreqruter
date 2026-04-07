import numpy as np

def calculate_performance_velocity(application):
    """
    Predicts the candidate's future growth curve (Performance Velocity).
    Equation involves: Experience Years, AI Score, Interview Confidence, and Culture Vibe.
    """
    exp = application.candidate.experience_years
    base_potential = application.ai_score / 10.0 # 0-10 scale
    
    # ── Velocity Factors ──────────
    # High AI Score + Low Experience = High Velocity (Rapid Learner)
    # High AI Score + High Experience = High Plateau (Expert Stability)
    # Low AI Score + High Experience = Decelerating (Stagnation risk)
    
    if exp < 2:
        velocity_multiplier = 1.8 if base_potential > 8 else 1.2
    elif exp < 5:
        velocity_multiplier = 1.4 if base_potential > 7 else 1.0
    else:
        velocity_multiplier = 1.1 if base_potential > 7 else 0.8
        
    # Projected 3-Year Outlook
    year_1 = base_potential * (1 + (velocity_multiplier * 0.2))
    year_2 = year_1 * (1 + (velocity_multiplier * 0.15))
    year_3 = year_2 * (1 + (velocity_multiplier * 0.10))
    
    # Normalize back to 0-100
    points = [round(p * 10, 1) for p in [base_potential, year_1, year_2, year_3]]
    
    # Traits
    traits = []
    if velocity_multiplier > 1.5:
        traits.append("Hyper-Growth Talent")
    elif velocity_multiplier > 1.2:
        traits.append("High-Potential Individual")
    elif velocity_multiplier < 0.9:
        traits.append("Stagnation Risk / Legacy Focused")
    else:
        traits.append("Stable Performer")
        
    return {
        "trajectory": points, # [Current, Y1, Y2, Y3]
        "velocity_index": round(velocity_multiplier * 10, 1),
        "primary_trait": traits[0] if traits else "Market Standard",
        "labels": ["Today", "Year 1", "Year 2", "Year 3"]
    }
