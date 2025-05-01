# backend/chapters/management/commands/load_sample_data.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from chapters.models import Chapter, Word
from patients.models import Patient
from progress.models import Progress, SessionHistory
from django.utils import timezone
from datetime import timedelta
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Load sample data for demonstration'

    def handle(self, *args, **kwargs):
        # Create a doctor user
        doctor, created = User.objects.get_or_create(
            username='doctor',
            defaults={
                'email': 'doctor@example.com',
                'slmc_id': 'SLMC1234',
                'is_doctor': True,
            }
        )
        if created:
            doctor.set_password('password123')
            doctor.save()
            self.stdout.write(self.style.SUCCESS(f'Created doctor user: {doctor.username}'))
        
        # Create chapters and words based on phonemes
        phonemes_data = [
            {
                'chapter_number': 1,
                'name': 'P Sound',
                'words': [
                    'pen', 'apple', 'stop', 'people', 'pepper', 'puppy', 'paper',
                    'purple', 'spoon', 'spot', 'speak', 'jump', 'lamp', 'tape', 'help'
                ]
            },
            {
                'chapter_number': 2,
                'name': 'B Sound',
                'words': [
                    'ball', 'baby', 'book', 'bird', 'boat', 'box', 'blue',
                    'bread', 'bear', 'rabbit', 'table', 'rubber', 'bubble', 'grab', 'crab'
                ]
            },
            {
                'chapter_number': 3,
                'name': 'T Sound',
                'words': [
                    'time', 'water', 'cat', 'tiger', 'tree', 'train', 'top',
                    'butter', 'letter', 'bottle', 'turtle', 'teacher', 'today', 'twenty', 'star'
                ]
            },
            {
                'chapter_number': 4,
                'name': 'D Sound',
                'words': [
                    'dog', 'red', 'bed', 'door', 'day', 'duck', 'desk',
                    'daddy', 'dinner', 'under', 'ladder', 'candy', 'bird', 'hand', 'land'
                ]
            },
            {
                'chapter_number': 5,
                'name': 'K Sound',
                'words': [
                    'cat', 'book', 'duck', 'key', 'cake', 'car', 'cookie',
                    'kite', 'king', 'sock', 'back', 'chicken', 'truck', 'black', 'clock'
                ]
            }
        ]
        
        for chapter_data in phonemes_data:
            chapter, created = Chapter.objects.get_or_create(
                chapter_number=chapter_data['chapter_number'],
                defaults={'name': chapter_data['name']}
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created chapter: {chapter.name}'))
            
            # Add words to the chapter
            for idx, word_text in enumerate(chapter_data['words'], 1):
                word, created = Word.objects.get_or_create(
                    chapter=chapter,
                    word=word_text,
                    defaults={'order': idx}
                )
                if created:
                    self.stdout.write(f'  Added word: {word_text}')
        
        # Create a patient
        patient, created = Patient.objects.get_or_create(
            patient_id='PAT001',
            defaults={
                'full_name': 'John Doe',
                'gender': 'Male',
                'doctor': doctor,
                'first_clinic_date': timezone.now() - timedelta(days=30)
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created patient: {patient.full_name}'))
        
        # Create progress data
        for chapter in Chapter.objects.all()[:3]:  # First 3 chapters
            words = chapter.words.all()
            for word in words:
                # Create multiple progress entries for each word
                num_trials = random.randint(1, 5)
                for trial in range(1, num_trials + 1):
                    accuracy = random.uniform(70.0 if trial == 1 else 80.0, 100.0)
                    date = timezone.now() - timedelta(days=random.randint(1, 30))
                    
                    Progress.objects.create(
                        patient=patient,
                        word=word,
                        trial_number=trial,
                        accuracy=accuracy,
                        date=date.date(),
                        time=date.time()
                    )
        
        # Create session history
        sessions_data = [
            {'date': timezone.now() - timedelta(days=2), 'duration': '45 min', 'score': 85},
            {'date': timezone.now() - timedelta(days=5), 'duration': '60 min', 'score': 92},
            {'date': timezone.now() - timedelta(days=7), 'duration': '30 min', 'score': 78},
            {'date': timezone.now() - timedelta(days=10), 'duration': '40 min', 'score': 88},
            {'date': timezone.now() - timedelta(days=14), 'duration': '55 min', 'score': 90},
        ]
        
        for session_data in sessions_data:
            SessionHistory.objects.create(
                patient=patient,
                date=session_data['date'].date(),
                duration=session_data['duration'],
                score=session_data['score']
            )
        
        self.stdout.write(self.style.SUCCESS('Successfully loaded sample data'))