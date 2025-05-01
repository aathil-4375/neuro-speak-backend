from django.urls import path
from .views import DoctorSignUpView

urlpatterns = [
    path('api/doctors/signup/', DoctorSignUpView.as_view(), name='doctor_signup'),
]
