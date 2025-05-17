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

# Enhanced progress calculation for PatientProgressSummaryView
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
                word_count = words.count()
                if word_count == 0:
                    continue  # Skip chapters with no words
                
                completed_words = 0
                attempted_words = 0
                total_word_accuracies = 0
                total_chapter_accuracy = 0
                chapter_accuracy_count = 0
                last_practiced = None
                has_progress = False
                highest_word_accuracy = 0
                
                # Check progress for each word in the chapter
                for word in words:
                    progress_records = Progress.objects.filter(
                        patient=patient,
                        word=word
                    ).order_by('-date', '-time')
                    
                    if progress_records.exists():
                        has_progress = True
                        attempted_words += 1
                        latest_record = progress_records.first()
                        
                        # Track the highest accuracy for any word
                        if latest_record.accuracy > highest_word_accuracy:
                            highest_word_accuracy = latest_record.accuracy
                        
                        if latest_record.accuracy >= 90:  # Consider 90%+ as completed
                            completed_words += 1
                        
                        total_chapter_accuracy += latest_record.accuracy
                        chapter_accuracy_count += 1
                        
                        # Track total accuracies to calculate average
                        total_word_accuracies += latest_record.accuracy
                        
                        if not last_practiced or latest_record.date > last_practiced:
                            last_practiced = latest_record.date
                
                # Calculate chapter progress percentage
                if completed_words == word_count:
                    # All words completed (mastered)
                    progress_percentage = 100.0
                elif has_progress:
                    # Enhanced progress calculation for in-progress chapters:
                    # 1. Base progress from completed words
                    completion_progress = (completed_words / word_count) * 100.0
                    
                    # 2. Progress from attempted words (max 20%)
                    attempt_progress = (attempted_words / word_count) * 20.0
                    
                    # 3. Progress from highest word accuracy (gives credit for almost completed words)
                    accuracy_progress = 0
                    if highest_word_accuracy > 90:  # Changed from 50 to 90
                        accuracy_progress = (highest_word_accuracy - 90) * 2  # Adjusted calculation based on new threshold
                    
                    # 4. Progress from average accuracy across all attempted words
                    avg_accuracy = 0
                    if attempted_words > 0:
                        avg_accuracy = total_word_accuracies / attempted_words
                        avg_accuracy_progress = avg_accuracy * 0.15  # Up to 15% more from average accuracy
                    else:
                        avg_accuracy_progress = 0
                    
                    # 5. Combine all progress factors with minimum 10% for any in-progress chapter
                    progress_percentage = max(
                        10.0,  # Minimum 10% for in-progress
                        completion_progress +  # Full credit for completed words
                        (attempt_progress * 0.25) +  # 25% credit for attempted words
                        accuracy_progress +  # Credit for highest word accuracy
                        avg_accuracy_progress  # Credit for average accuracy
                    )
                    
                    # Cap at 90% for in-progress chapters (leaves room for completion)
                    if progress_percentage > 90 and completed_words < word_count:
                        progress_percentage = 90.0  # Changed from 95 to 90
                else:
                    # No progress
                    progress_percentage = 0.0
                
                # Determine chapter status
                if completed_words == word_count:
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