from rest_framework import serializers
from .models import JobPosting, Candidate, Application, Interview, Technology

class TechnologySerializer(serializers.ModelSerializer):
    class Meta:
        model = Technology
        fields = ['id', 'name', 'icon_class', 'color']

class JobPostingSerializer(serializers.ModelSerializer):
    technology = TechnologySerializer(read_only=True)
    class Meta:
        model = JobPosting
        fields = '__all__'

class CandidateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidate
        fields = '__all__'

class ApplicationSerializer(serializers.ModelSerializer):
    job = JobPostingSerializer(read_only=True)
    candidate = CandidateSerializer(read_only=True)
    class Meta:
        model = Application
        fields = '__all__'

class InterviewSerializer(serializers.ModelSerializer):
    application = ApplicationSerializer(read_only=True)
    class Meta:
        model = Interview
        fields = '__all__'
