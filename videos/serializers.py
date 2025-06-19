from rest_framework import serializers
from .models import Video

class VideoSerializer(serializers.ModelSerializer):
    video_url = serializers.SerializerMethodField()
    file_size_mb = serializers.SerializerMethodField()
    
    class Meta:
        model = Video
        fields = ['id', 'title', 'description', 'video_file', 'video_url', 
                 'uploaded_at', 'file_size', 'file_size_mb']
        read_only_fields = ['uploaded_at', 'file_size']
    
    def get_video_url(self, obj):
        if obj.video_file:
            return obj.video_file.url
        return None
    
    def get_file_size_mb(self, obj):
        if obj.file_size:
            return round(obj.file_size / (1024 * 1024), 2)
        return None
    
    def validate_video_file(self, value):
        # Validate file size (50MB limit)
        if value.size > 50 * 1024 * 1024:
            raise serializers.ValidationError("Video file too large. Maximum size is 50MB.")
        
        # Validate file type
        allowed_types = ['video/mp4', 'video/avi', 'video/mov', 'video/wmv', 'video/quicktime']
        if value.content_type not in allowed_types:
            raise serializers.ValidationError("Unsupported video format. Allowed: MP4, AVI, MOV, WMV")
        
        return value

class VideoUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = ['title', 'description', 'video_file']