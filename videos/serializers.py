# videos/serializers.py
from rest_framework import serializers
from .models import VideoUpload, VideoProgress
from patients.serializers import PatientSerializer
from chapters.serializers import ChapterSerializer, WordSerializer

class VideoUploadSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    chapter = ChapterSerializer(read_only=True)
    word = WordSerializer(read_only=True)
    video_url = serializers.SerializerMethodField()
    
    class Meta:
        model = VideoUpload
        fields = [
            'id', 'patient', 'chapter', 'word', 'language', 'video_type',
            'video_file', 'video_url', 'uploaded_at', 'trial_number',
            'accuracy_score', 'duration', 'is_approved', 's3_key'
        ]
        read_only_fields = ['uploaded_at', 's3_key']
    
    def get_video_url(self, obj):
        if obj.video_file:
            return obj.video_file.url
        return None

class VideoUploadCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoUpload
        fields = [
            'patient', 'chapter', 'word', 'language', 'video_type',
            'video_file', 'trial_number'
        ]
    
    def create(self, validated_data):
        # Generate S3 key
        patient = validated_data['patient']
        chapter = validated_data['chapter']
        word = validated_data['word']
        language = validated_data['language']
        video_type = validated_data['video_type']
        trial_number = validated_data.get('trial_number', 1)
        
        s3_key = f"{patient.patient_id}/{chapter.chapter_number}/{word.word}/{language}_{video_type}_{trial_number}.mp4"
        validated_data['s3_key'] = s3_key
        
        return super().create(validated_data)

class VideoProgressSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    chapter = ChapterSerializer(read_only=True)
    word = WordSerializer(read_only=True)
    
    class Meta:
        model = VideoProgress
        fields = [
            'id', 'patient', 'chapter', 'word', 'language', 'current_trial',
            'best_accuracy', 'completed', 'last_attempt'
        ]
        read_only_fields = ['last_attempt'] 