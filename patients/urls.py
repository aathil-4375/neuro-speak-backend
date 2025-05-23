# patients/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.PatientListCreateView.as_view(), name='patient-list-create'),
    path('search/', views.PatientSearchView.as_view(), name='patient-search'),
    path('<str:patient_id>/', views.PatientDetailView.as_view(), name='patient-detail'),
]
