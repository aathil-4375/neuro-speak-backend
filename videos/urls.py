# videos/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('uploads/', views.VideoUploadListCreateView.as_view(), name='video-upload-list'),
    path('uploads/<int:pk>/', views.VideoUploadDetailView.as_view(), name='video-upload-detail'),
    path('progress/', views.VideoProgressListView.as_view(), name='video-progress-list'),
    path('upload-patient-video/', views.upload_patient_video, name='upload-patient-video'),
    path('reference-videos/', views.get_reference_videos, name='get-reference-videos'),
    path('chapter-words/', views.get_chapter_words, name='get-chapter-words'),
    path('patient-progress/<str:patient_id>/', views.get_patient_progress, name='get-patient-progress'),
] 