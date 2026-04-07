"""
Culture Fit Simulation Service — SmartRecruit
Generates dynamic, branching workplace scenarios to test soft skills, 
conflict resolution, and cultural alignment.
"""

SCENARIOS = {
    "Technical Debt vs. Deadline": {
        "text": "Your team is 48 hours away from a major production release. You discover a critical architectural mistake that will likely cause a 5% performance drop for users, but fixing it will delay the launch by 2 weeks. The marketing team has already spent ₹50L on the launch campaign. What do you do?",
        "options": [
            {
                "id": "A",
                "text": "Ship as is, and schedule a patch for next month. Business continuity first.",
                "vibe_impact": {"Pragmatism": 15, "Speed": 20, "Quality": -10}
            },
            {
                "id": "B",
                "text": "Call an emergency meeting with Stakeholders. Be honest about the performance debt and ask for guidance.",
                "vibe_impact": {"Transparency": 20, "Collaboration": 15, "Leadership": 10}
            },
            {
                "id": "C",
                "text": "Stay overnight with the team and attempt a 'hacky' fix that mitigates 80% of the drop without delay.",
                "vibe_impact": {"Tenacity": 25, "Hustle": 20, "Risk": 15}
            }
        ]
    },
    "The Interpersonal Conflict": {
        "text": "A senior developer (who is the only one who knows the legacy system) is being constantly dismissive and rude to a junior hire during code reviews. This is affecting team morale. You are the project lead. How do you handle this?",
        "options": [
            {
                "id": "A",
                "text": "Talk to the Senior dev privately. Acknowledge their value but firmly set expectations for professional conduct.",
                "vibe_impact": {"Directness": 20, "Empathy": 10, "Conflict Resolution": 20}
            },
            {
                "id": "B",
                "text": "Publicly call out the behavior in the next stand-up to show that bullying is not tolerated.",
                "vibe_impact": {"Courage": 15, "Safety": -10, "Team Vibe": -15}
            },
            {
                "id": "C",
                "text": "Ask the Junior hire to 'toughen up' and focus on the technical feedback, ignoring the tone.",
                "vibe_impact": {"Efficiency": 10, "Retention_Risk": 25, "Culture_Red_Flag": 20}
            }
        ]
    }
}

def get_next_scenario(current_index=0):
    keys = list(SCENARIOS.keys())
    if current_index >= len(keys):
        return None
    
    key = keys[current_index]
    scenario = SCENARIOS[key]
    return {
        "id": key,
        "text": scenario["text"],
        "options": [{"id": o["id"], "text": o["text"]} for o in scenario["options"]]
    }

def calculate_vibe_score(responses):
    """
    Simulates AI analysis of the candidate's choices.
    """
    aggregate = {"Empathy": 50, "Speed": 50, "Quality": 50, "Leadership": 50, "Ethics": 50}
    
    for resp in responses:
        scenario_key = resp.get('scenario_id')
        option_id = resp.get('option_id')
        
        if scenario_key in SCENARIOS:
            for opt in SCENARIOS[scenario_key]["options"]:
                if opt["id"] == option_id:
                    for trait, impact in opt["vibe_impact"].items():
                        # We don't just add, we blend
                        if trait in aggregate:
                            aggregate[trait] = max(0, min(100, aggregate[trait] + impact))
                        else:
                            aggregate[trait] = 50 + impact
                            
    return aggregate
