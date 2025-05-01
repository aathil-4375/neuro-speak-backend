# backend/patients/admin.py
from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import Patient

User = get_user_model()

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'patient_id', 'gender', 'doctor', 'first_clinic_date')
    list_filter = ('gender', 'doctor', 'first_clinic_date')
    search_fields = ('full_name', 'patient_id')
    ordering = ('full_name',)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "doctor":
            # Only show doctors in the dropdown
            kwargs["queryset"] = User.objects.filter(is_doctor=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)