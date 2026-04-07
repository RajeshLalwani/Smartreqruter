from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone

class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0049_candidate_pseudonym_alter_badge_rarity'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('audit_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('fairness_score', models.FloatField(default=0.0)),
                ('disparate_impact_ratio', models.FloatField(default=1.0)),
                ('equal_opportunity_diff', models.FloatField(default=0.0)),
                ('demographics_json', models.JSONField(blank=True, default=dict)),
                ('is_certified', models.BooleanField(default=False)),
                ('audit_report', models.TextField(blank=True)),
                ('has_risk', models.BooleanField(default=False)),
                ('risk_details', models.JSONField(blank=True, default=list)),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bias_audits', to='jobs.jobposting')),
            ],
            options={
                'ordering': ['-audit_date'],
            },
        ),
    ]
