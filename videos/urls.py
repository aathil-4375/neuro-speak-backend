from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.VideoUploadView.as_view(), name='video-upload'),
    path('upload-simple/', views.upload_video_simple, name='video-upload-simple'),
    path('test-upload/', views.test_video_upload, name='test-video-upload'),
    path('list/', views.VideoListView.as_view(), name='video-list'),
    path('<int:pk>/', views.VideoDetailView.as_view(), name='video-detail'),
]