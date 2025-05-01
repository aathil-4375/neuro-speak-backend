# backend/progress/serializers.py
from rest_framework import serializers
from .models import Progress, SessionHistory
from patients.serializers import PatientSerializer
from chapters.serializers import WordSerializer

class ProgressSerializer(serializers.ModelSerializer):
    patient_detail = PatientSerializer(source='patient', read_only=True)
    word_detail = WordSerializer(source='word', read_only=True)
    
    class Meta:
        model = Progress
        fields = ['id', 'patient', 'patient_detail', 'word', 'word_detail', 
                  'trial_number', 'accuracy', 'date', 'time']
        read_only_fields = ['time']

class SessionHistorySerializer(serializers.ModelSerializer):
    patient_detail = PatientSerializer(source='patient', read_only=True)
    
    class Meta:
        model = SessionHistory
        fields = ['id', 'patient', 'patient_detail', 'date', 'duration', 'score']