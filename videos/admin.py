# videos/admin.py
from django.contrib import admin
from .models import VideoUpload, VideoProgress

@admin.register(VideoUpload)
class VideoUploadAdmin(admin.ModelAdmin):
    list_display = ['patient', 'chapter', 'word', 'language', 'video_type', 'trial_number', 'accuracy_score', 'uploaded_at']
    list_filter = ['language', 'video_type', 'is_approved', 'uploaded_at']
    search_fields = ['patient__patient_id', 'patient__full_name', 'word__word']
    readonly_fields = ['s3_key', 'uploaded_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('patient', 'chapter', 'word')

@admin.register(VideoProgress)
class VideoProgressAdmin(admin.ModelAdmin):
    list_display = ['patient', 'chapter', 'word', 'language', 'current_trial', 'best_accuracy', 'completed', 'last_attempt']
    list_filter = ['language', 'completed', 'last_attempt']
    search_fields = ['patient__patient_id', 'patient__full_name', 'word__word']
    readonly_fields = ['last_attempt']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('patient', 'chapter', 'word') 