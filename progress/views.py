# backend/progress/views.py
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Avg, Count, Max
from django.utils import timezone
from .models import Progress, SessionHistory
from .serializers import ProgressSerializer, SessionHistorySerializer
from patients.models import Patient
from chapters.models import Chapter, Word

class ProgressListCreateView(generics.ListCreateAPIView):
    """List and create progress entries"""
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ProgressSerializer
    
    def get_queryset(self):
        return Progress.objects.filter(patient__doctor=self.request.user)

class PatientProgressView(APIView):
    """Get progress for a specific patient"""
    permission_classes = (permissions.IsAuthenticated,)
    
    def get(self, request, patient_id):
        try:
            patient = Patient.objects.get(patient_id=patient_id, doctor=request.user)
            progress = Progress.objects.filter(patient=patient)
            serializer = ProgressSerializer(progress, many=True)
            return Response(serializer.data)
        except Patient.DoesNotExist:
            return Response({'error': 'Patient not found'}, status=status.HTTP_404_NOT_FOUND)

class GraphDataView(APIView):
    """Get graph data for a patient"""
    permission_classes = (permissions.IsAuthenticated,)
    
    def get(self, request, patient_id):
        try:
            patient = Patient.objects.get(patient_id=patient_id, doctor=request.user)
            progress = Progress.objects.filter(patient=patient).order_by('date', 'time')
            
            # Format data for graph
            data = []
            for record in progress:
                data.append({
                    'date': record.date.strftime('%Y-%m-%d'),
                    'accuracy': record.accuracy,
                    'word': record.word.word,
                    'chapter': record.word.chapter.chapter_number
                })
            
            return Response(data)
        except Patient.DoesNotExist:
            return Response({'error': 'Patient not found'}, status=status.HTTP_404_NOT_FOUND)

class SessionHistoryView(APIView):
    """Get session history for a patient"""
    permission_classes = (permissions.IsAuthenticated,)
    
    def get(self, request, patient_id):
        try:
            patient = Patient.objects.get(patient_id=patient_id, doctor=request.user)
            sessions = SessionHistory.objects.filter(patient=patient).order_by('-date')
            serializer = SessionHistorySerializer(sessions, many=True)
            return Response(serializer.data)
        except Patient.DoesNotExist:
            return Response({'error': 'Patient not found'}, status=status.HTTP_404_NOT_FOUND)

class PatientProgressSummaryView(APIView):
    """Get formatted data for frontend display - matching PatientUser.jsx"""
    permission_classes = (permissions.IsAuthenticated,)
    
    def get(self, request, patient_id):
        try:
            patient = Patient.objects.get(patient_id=patient_id, doctor=request.user)
            
            # Get phoneme progress data
            phoneme_progress = []
            chapters = Chapter.objects.all().order_by('chapter_number')
            
            # Initialize counters for statistics
            completed_chapters = 0
            in_progress_chapters = 0
            not_started_chapters = 0
            total_accuracy = 0
            accuracy_count = 0
            
            for chapter in chapters:
                words = chapter.words.all()
                completed_words = 0
                total_chapter_accuracy = 0
                chapter_accuracy_count = 0
                last_practiced = None
                has_progress = False
                
                # Check progress for each word in the chapter
                for word in words:
                    progress_records = Progress.objects.filter(
                        patient=patient,
                        word=word
                    ).order_by('-date', '-time')
                    
                    if progress_records.exists():
                        has_progress = True
                        latest_record = progress_records.first()
                        if latest_record.accuracy >= 90:  # Consider 90%+ as completed
                            completed_words += 1
                        
                        total_chapter_accuracy += latest_record.accuracy
                        chapter_accuracy_count += 1
                        
                        if not last_practiced or latest_record.date > last_practiced:
                            last_practiced = latest_record.date
                
                # Calculate chapter progress and status
                word_count = words.count()
                if word_count > 0:
                    progress_percentage = (completed_words / word_count) * 100
                else:
                    progress_percentage = 0
                
                # Determine chapter status
                if word_count > 0 and completed_words == word_count:
                    status = 'completed'
                    completed_chapters += 1
                elif has_progress:
                    status = 'in-progress'
                    in_progress_chapters += 1
                else:
                    status = 'not-started'
                    not_started_chapters += 1
                
                # Calculate average accuracy
                if chapter_accuracy_count > 0:
                    chapter_accuracy = float(total_chapter_accuracy) / float(chapter_accuracy_count)
                    total_accuracy += chapter_accuracy
                    accuracy_count += 1
                else:
                    chapter_accuracy = 0.0
                
                # Get example words (first 3)
                example_words = list(words.values_list('word', flat=True)[:3])
                
                phoneme_progress.append({
                    'id': chapter.chapter_number,
                    'phoneme': f'/{chapter.name[0].lower()}/',
                    'exampleWords': example_words,
                    'status': status,
                    'progress': round(float(progress_percentage), 1),
                    'accuracy': round(float(chapter_accuracy), 1),
                    'lastPracticed': last_practiced.strftime('%Y-%m-%d') if last_practiced else None
                })
            
            # Get recent sessions
            recent_sessions = SessionHistory.objects.filter(patient=patient).order_by('-date')[:10]
            sessions_data = []
            
            for session in recent_sessions:
                # Extract phonemes from progress records for that date
                progress_on_date = Progress.objects.filter(
                    patient=patient,
                    date=session.date
                ).select_related('word__chapter')
                
                phonemes_practiced = set()
                words_attempted = 0
                
                for progress in progress_on_date:
                    chapter = progress.word.chapter
                    phonemes_practiced.add(f'/{chapter.name[0].lower()}/')
                    words_attempted += 1
                
                sessions_data.append({
                    'date': session.date.strftime('%Y-%m-%d'),
                    'duration': session.duration,
                    'phonemesPracticed': list(phonemes_practiced),
                    'wordsAttempted': words_attempted,
                    'accuracy': round(float(session.score), 1)  # Convert to float and round
                })
            
            # Calculate overall average accuracy
            if accuracy_count > 0:
                average_accuracy = float(total_accuracy) / float(accuracy_count)
            else:
                average_accuracy = 0.0
            
            response_data = {
                'patient': {
                    'id': patient.id,
                    'full_name': patient.full_name,
                    'patient_id': patient.patient_id,
                    'gender': patient.gender,
                    'first_clinic_date': patient.first_clinic_date.strftime('%Y-%m-%d'),
                },
                'phonemeProgress': phoneme_progress,
                'recentSessions': sessions_data,
                'statistics': {
                    'total_sessions': recent_sessions.count(),
                    'average_accuracy': round(float(average_accuracy), 1),
                    'completed_phonemes': completed_chapters,
                    'in_progress_phonemes': in_progress_chapters,
                    'not_started_phonemes': not_started_chapters
                }
            }
            
            return Response(response_data)
            
        except Patient.DoesNotExist:
            return Response({'error': 'Patient not found'}, status=status.HTTP_404_NOT_FOUND)

class ChapterWordProgressView(APIView):
    """Get word progress for GraphTab.jsx"""
    permission_classes = (permissions.IsAuthenticated,)
    
    def get(self, request, patient_id, chapter_number, word_text):
        try:
            patient = Patient.objects.get(patient_id=patient_id, doctor=request.user)
            chapter = Chapter.objects.get(chapter_number=chapter_number)
            word = Word.objects.get(chapter=chapter, word=word_text)
            
            # Get all progress records for this word
            progress_records = Progress.objects.filter(
                patient=patient,
                word=word
            ).order_by('date', 'time')
            
            trials = []
            for record in progress_records:
                trials.append({
                    'year': record.date.year,
                    'month': record.date.strftime("%B"),
                    'date': record.date.day,
                    'trial': record.trial_number,
                    'accuracy': round(float(record.accuracy), 1)  # Round to 1 decimal place
                })
            
            # Ensure the data format matches what GraphTab.jsx expects
            response_data = {
                'chapter': chapter_number,
                'word': word_text,
                'trials': trials
            }
            
            return Response(response_data)
            
        except (Patient.DoesNotExist, Chapter.DoesNotExist, Word.DoesNotExist):
            return Response({'error': 'Data not found'}, status=status.HTTP_404_NOT_FOUND)

class ChapterWordsView(APIView):
    """Get all words for a chapter - for ChapterPage.jsx"""
    permission_classes = (permissions.IsAuthenticated,)
    
    def get(self, request, chapter_number):
        try:
            chapter = Chapter.objects.get(chapter_number=chapter_number)
            words = list(chapter.words.all().order_by('order').values_list('word', flat=True))
            
            # Extract phoneme from chapter name
            phoneme = f'/{chapter.name[0].lower()}/'
            
            response_data = {
                'chapter': chapter_number,
                'phoneme': phoneme,
                'words': words
            }
            
            return Response(response_data)
            
        except Chapter.DoesNotExist:
            return Response({'error': 'Chapter not found'}, status=status.HTTP_404_NOT_FOUND)

class ProgressCreateView(generics.CreateAPIView):
    """Create progress entries (for mobile app to use)"""
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ProgressSerializer
    queryset = Progress.objects.all()

class SessionHistoryCreateView(generics.CreateAPIView):
    """Create session history entries (for mobile app to use)"""
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = SessionHistorySerializer
    queryset = SessionHistory.objects.all()