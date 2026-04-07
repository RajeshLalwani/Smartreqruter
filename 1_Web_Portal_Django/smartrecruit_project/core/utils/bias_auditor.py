import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder
from django.db.models import Avg, Count, Q
from jobs.models import Application, Candidate, JobPosting, BiasAuditLog
import logging

logger = logging.getLogger(__name__)

class BiasAuditor:
    def __init__(self, job_id):
        self.job = JobPosting.objects.get(id=job_id)
        self.applications = Application.objects.filter(job=self.job).select_related('candidate')

    def calculate_disparate_impact(self, protected_attr='gender', protected_value='FEMALE', reference_value='MALE'):
        """
        Calculates Disparate Impact Ratio (DIR).
        DIR = (Selection Rate of Protected Group) / (Selection Rate of Reference Group)
        """
        # Selection Rate of Protected Group
        total_p = self.applications.filter(**{f'candidate__{protected_attr}': protected_value}).count()
        selected_p = self.applications.filter(
            **{f'candidate__{protected_attr}': protected_value},
            ai_score__gte=70
        ).count()

        # Selection Rate of Reference Group
        total_r = self.applications.filter(**{f'candidate__{protected_attr}': reference_value}).count()
        selected_r = self.applications.filter(
            **{f'candidate__{protected_attr}': reference_value},
            ai_score__gte=70
        ).count()

        if total_p == 0 or total_r == 0: return 1.0
        sr_p = selected_p / total_p
        sr_r = selected_r / total_r
        return sr_p / sr_r if sr_r > 0 else 1.0

    def get_group_stats(self, attr='gender'):
        """Computes score distribution for charts."""
        stats = self.applications.values(f'candidate__{attr}').annotate(avg_score=Avg('ai_score'))
        return {item[f'candidate__{attr}']: round(item['avg_score'], 1) for item in stats}

    def analyze_correlations(self):
        data = []
        for app in self.applications:
            data.append({
                'loc': app.candidate.current_location,
                'tier': app.candidate.institution_type,
                'score': app.ai_score
            })
        if len(data) < 5: return {}
        df = pd.DataFrame(data)
        le = LabelEncoder()
        df['loc_enc'] = le.fit_transform(df['loc'])
        df['tier_enc'] = le.fit_transform(df['tier'])
        corr = df[['loc_enc', 'tier_enc', 'score']].corr()['score'].to_dict()
        return {'location': round(corr.get('loc_enc', 0), 2), 'tier': round(corr.get('tier_enc', 0), 2)}

    def generate_audit_report(self):
        dir_val = self.calculate_disparate_impact()
        corrs = self.analyze_correlations()
        group_stats = self.get_group_stats()
        
        score_dev = abs(1.0 - dir_val) * 100
        fairness_score = max(0, 100 - score_dev)
        has_risk = dir_val < 0.8
        
        log = BiasAuditLog.objects.create(
            job=self.job,
            fairness_score=fairness_score,
            disparate_impact_ratio=round(dir_val, 2),
            demographics_json={
                'correlations': corrs,
                'group_stats': group_stats,
                'chart_labels': list(group_stats.keys()),
                'chart_data': list(group_stats.values())
            },
            has_risk=has_risk,
            risk_details=["Bias Warning: Gender selection rate fails 80% rule."] if has_risk else [],
            is_certified=not has_risk
        )
        return log

def run_bias_audit(job_id):
    auditor = BiasAuditor(job_id)
    return auditor.generate_audit_report()
