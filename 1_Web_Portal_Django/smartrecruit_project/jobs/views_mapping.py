import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .views_advanced import _recruiter_required

@login_required
def talent_mapping_flow(request):
    """
    Talent Mapping: Visualizing migration patterns between companies.
    """
    if not _recruiter_required(request):
        return redirect('dashboard')
        
    # Simulated Graph Data: Nodes (Companies) and Edges (Talent Flow)
    mapping_data = {
        "nodes": [
            {"id": "YourCompany", "label": "SmartRecruit AI", "type": "target", "talent_count": 450},
            {"id": "CompA", "label": "TechGiant X", "type": "source", "talent_count": 5000},
            {"id": "CompB", "label": "Startup Y", "type": "flux", "talent_count": 200},
            {"id": "CompC", "label": "Legacy Corp Z", "type": "source", "talent_count": 12000}
        ],
        "edges": [
            {"from": "CompA", "to": "YourCompany", "volume": 15, "reason": "Salary Growth"},
            {"from": "CompB", "to": "YourCompany", "volume": 8, "reason": "Stock Options"},
            {"from": "CompC", "to": "CompA", "volume": 45, "reason": "Tech Stack Upgrade"},
            {"from": "CompC", "to": "YourCompany", "volume": 12, "reason": "Remote Culture"}
        ]
    }
    
    return render(request, 'jobs/talent_mapping.html', {
        'graph': mapping_data
    })
