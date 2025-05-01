# backend/patients/models.py
from django.db import models
from django.conf import settings

class Patient(models.Model):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]
    
    full_name = models.CharField(max_length=255)
    patient_id = models.CharField(max_length=50, unique=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='patients')
    first_clinic_date = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.patient_id} - {self.full_name}"
    
    class Meta:
        ordering = ['patient_id']