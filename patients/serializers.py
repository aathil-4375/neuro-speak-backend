# backend/patients/serializers.py
from rest_framework import serializers
from .models import Patient
from users.serializers import UserSerializer

class PatientSerializer(serializers.ModelSerializer):
    doctor_detail = UserSerializer(source='doctor', read_only=True)
    
    class Meta:
        model = Patient
        fields = ['id', 'full_name', 'patient_id', 'gender', 'doctor', 
                  'doctor_detail', 'first_clinic_date']
        extra_kwargs = {
            'doctor': {'required': False}  # Make doctor field optional
        }
    
    def create(self, validated_data):
        # If doctor is not provided, use the current user
        if 'doctor' not in validated_data:
            request = self.context.get('request')
            if request and hasattr(request, 'user'):
                validated_data['doctor'] = request.user
        return super().create(validated_data)