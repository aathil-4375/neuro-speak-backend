# videos/views.py
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.conf import settings
import boto3
import os
from .models import VideoUpload, VideoProgress
from .serializers import VideoUploadSerializer, VideoUploadCreateSerializer, VideoProgressSerializer
from patients.models import Patient
from chapters.models import Chapter, Word

class VideoUploadListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = VideoUploadSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_doctor:
            # Doctors can see all videos
            return VideoUpload.objects.all()
        else:
            # Patients can only see their own videos
            try:
                patient = Patient.objects.get(patient_id=user.username)
                return VideoUpload.objects.filter(patient=patient)
            except Patient.DoesNotExist:
                return VideoUpload.objects.none()
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return VideoUploadCreateSerializer
        return VideoUploadSerializer

class VideoUploadDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = VideoUpload.objects.all()
    serializer_class = VideoUploadSerializer

class VideoProgressListView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = VideoProgressSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_doctor:
            return VideoProgress.objects.all()
        else:
            try:
                patient = Patient.objects.get(patient_id=user.username)
                return VideoProgress.objects.filter(patient=patient)
            except Patient.DoesNotExist:
                return VideoProgress.objects.none()

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_patient_video(request):
    """Upload patient trial video and get ML accuracy score"""
    try:
        patient_id = request.data.get('patient_id')
        chapter_id = request.data.get('chapter_id')
        word_id = request.data.get('word_id')
        language = request.data.get('language')
        video_file = request.FILES.get('video_file')
        
        if not all([patient_id, chapter_id, word_id, language, video_file]):
            return Response({
                'error': 'Missing required fields'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        patient = get_object_or_404(Patient, patient_id=patient_id)
        chapter = get_object_or_404(Chapter, id=chapter_id)
        word = get_object_or_404(Word, id=word_id)
        
        # Get next trial number
        existing_trials = VideoUpload.objects.filter(
            patient=patient,
            chapter=chapter,
            word=word,
            language=language,
            video_type='patient_trial'
        ).count()
        trial_number = existing_trials + 1
        
        # Create video upload
        video_upload = VideoUpload.objects.create(
            patient=patient,
            chapter=chapter,
            word=word,
            language=language,
            video_type='patient_trial',
            video_file=video_file,
            trial_number=trial_number
        )
        
        # TODO: Send video to ML model for accuracy scoring
        # For now, simulate accuracy score
        accuracy_score = 85.5  # This should come from ML model
        
        video_upload.accuracy_score = accuracy_score
        video_upload.save()
        
        # Update or create progress
        progress, created = VideoProgress.objects.get_or_create(
            patient=patient,
            chapter=chapter,
            word=word,
            language=language,
            defaults={
                'current_trial': trial_number,
                'best_accuracy': accuracy_score,
                'completed': accuracy_score >= 80.0  # Threshold for completion
            }
        )
        
        if not created:
            progress.current_trial = trial_number
            if accuracy_score > progress.best_accuracy:
                progress.best_accuracy = accuracy_score
            if accuracy_score >= 80.0:
                progress.completed = True
            progress.save()
        
        return Response({
            'message': 'Video uploaded successfully',
            'accuracy_score': accuracy_score,
            'trial_number': trial_number,
            'should_retry': accuracy_score < 80.0,
            'video_id': video_upload.id
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_reference_videos(request):
    """Get reference video for a specific chapter and word (only one per word+language)"""
    try:
        chapter_id = request.GET.get('chapter_id')
        word_id = request.GET.get('word_id')
        language = request.GET.get('language', 'tamil')
        
        if not all([chapter_id, word_id]):
            return Response({
                'error': 'Missing chapter_id or word_id'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the single reference video for this word+language combination
        video = VideoUpload.objects.filter(
            chapter_id=chapter_id,
            word_id=word_id,
            language=language,
            video_type='reference'
        ).first()
        
        if video:
            serializer = VideoUploadSerializer(video)
            return Response(serializer.data)
        else:
            return Response({
                'error': 'Reference video not found for this word and language'
            }, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_chapter_words(request):
    """Get all words for a specific chapter with reference videos"""
    try:
        chapter_id = request.GET.get('chapter_id')
        language = request.GET.get('language', 'tamil')
        
        if not chapter_id:
            return Response({
                'error': 'Missing chapter_id'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get words for the chapter
        words = Word.objects.filter(chapter_id=chapter_id).order_by('order')
        
        # Get reference videos for each word (only one per word+language)
        words_with_videos = []
        for word in words:
            video = VideoUpload.objects.filter(
                chapter_id=chapter_id,
                word=word,
                language=language,
                video_type='reference'
            ).first()
            
            words_with_videos.append({
                'id': word.id,
                'word': word.word,
                'order': word.order,
                'has_reference_video': video is not None,
                'video_url': video.video_file.url if video else None,
                'reference_video_id': video.id if video else None,
            })
        
        return Response(words_with_videos)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_patient_progress(request, patient_id):
    """Get progress for a specific patient"""
    try:
        patient = get_object_or_404(Patient, patient_id=patient_id)
        progress = VideoProgress.objects.filter(patient=patient)
        serializer = VideoProgressSerializer(progress, many=True)
        return Response(serializer.data)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 