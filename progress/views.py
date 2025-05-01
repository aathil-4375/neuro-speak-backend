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
            
            for chapter in chapters:
                words = chapter.words.all()
                completed_words = 0
                total_accuracy = 0
                accuracy_count = 0
                last_practiced = None
                
                # Check progress for each word in the chapter
                for word in words:
                    progress_records = Progress.objects.filter(
                        patient=patient,
                        word=word
                    ).order_by('-date', '-time')
                    
                    if progress_records.exists():
                        latest_record = progress_records.first()
                        if latest_record.accuracy >= 90:  # Consider 90%+ as completed
                            completed_words += 1
                        
                        total_accuracy += latest_record.accuracy
                        accuracy_count += 1
                        
                        if not last_practiced or latest_record.date > last_practiced:
                            last_practiced = latest_record.date
                
                # Calculate chapter progress and status
                if words.count() > 0:
                    progress_percentage = (completed_words / words.count()) * 100
                else:
                    progress_percentage = 0
                
                if progress_percentage == 100:
                    status = 'completed'
                elif progress_percentage > 0:
                    status = 'in-progress'
                else:
                    status = 'not-started'
                
                # Calculate average accuracy
                if accuracy_count > 0:
                    chapter_accuracy = total_accuracy / accuracy_count
                else:
                    chapter_accuracy = 0
                
                # Get example words (first 3)
                example_words = list(words.values_list('word', flat=True)[:3])
                
                phoneme_progress.append({
                    'id': chapter.chapter_number,
                    'phoneme': f'/{chapter.name[0].lower()}/', # Extract phoneme from chapter name
                    'exampleWords': example_words,
                    'status': status,
                    'progress': round(progress_percentage),
                    'accuracy': round(chapter_accuracy),
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
                    'accuracy': round(session.score)
                })
            
            # Calculate overall statistics
            completed_chapters = sum(1 for p in phoneme_progress if p['status'] == 'completed')
            in_progress_chapters = sum(1 for p in phoneme_progress if p['status'] == 'in-progress')
            
            overall_accuracies = [p['accuracy'] for p in phoneme_progress if p['accuracy'] > 0]
            average_accuracy = sum(overall_accuracies) / len(overall_accuracies) if overall_accuracies else 0
            
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
                    'average_accuracy': round(average_accuracy),
                    'completed_phonemes': completed_chapters,
                    'in_progress_phonemes': in_progress_chapters,
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
                    'accuracy': round(record.accuracy)
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