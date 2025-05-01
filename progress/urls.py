from django.urls import path
from . import views

urlpatterns = [
    path('', views.ProgressListCreateView.as_view(), name='progress-list-create'),
    path('patient/<str:patient_id>/summary/', views.PatientProgressSummaryView.as_view(), name='patient-summary'),
    path('patient/<str:patient_id>/chapter/<int:chapter_number>/word/<str:word_text>/', 
         views.ChapterWordProgressView.as_view(), name='word-progress'),
    path('chapter/<int:chapter_number>/words/', views.ChapterWordsView.as_view(), name='chapter-words'),
    path('session-history/<str:patient_id>/', views.SessionHistoryView.as_view(), name='session-history'),
    
    # Additional endpoints for mobile app integration
    path('create/', views.ProgressCreateView.as_view(), name='progress-create'),
    path('session-history/create/', views.SessionHistoryCreateView.as_view(), name='session-history-create'),
]