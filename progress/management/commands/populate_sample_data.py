# backend/progress/management/commands/populate_sample_data.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta, time
import random
from chapters.models import Chapter, Word
from patients.models import Patient
from progress.models import Progress, SessionHistory
from users.models import User


class Command(BaseCommand):
    help = 'Populates sample data for demonstration'

    def handle(self, *args, **options):
        # Get the existing doctors from the Users list shown in the admin
        doctors = []
        
        # Create or get doctors based on the admin interface
        doctors_data = [
            {'username': 'DOC001', 'slmc_id': 'DOC001', 'first_name': 'Ahameth', 'last_name': 'Aathil'},
            {'username': 'DOC002', 'slmc_id': 'DOC002', 'first_name': 'Ravi', 'last_name': 'Muthu'},
            {'username': 'DOC003', 'slmc_id': 'DOC003', 'first_name': 'Suntharalingam', 'last_name': 'Sivanujan'},
        ]
        
        for doc_data in doctors_data:
            doctor, created = User.objects.get_or_create(
                username=doc_data['username'],
                defaults={
                    'slmc_id': doc_data['slmc_id'],
                    'is_doctor': True,
                    'first_name': doc_data['first_name'],
                    'last_name': doc_data['last_name'],
                    'email': f"{doc_data['username'].lower()}@example.com"
                }
            )
            doctors.append(doctor)
            self.stdout.write(f"{'Created' if created else 'Got'} doctor: {doctor.username}")
        
        # Get the admin user "aathil"
        admin_user, _ = User.objects.get_or_create(
            username='aathil',
            defaults={
                'email': 'ahamethaathil2@gmail.com',
                'is_staff': True,
                'is_superuser': True,
                'first_name': 'Aathil',
                'last_name': 'Admin'
            }
        )
        
        # Create or get patients based on the admin interface
        patients_data = [
            {'patient_id': 'PED001', 'full_name': 'Raja Mani', 'gender': 'Male', 'doctor': doctors[0]},
            {'patient_id': 'PED002', 'full_name': 'Vidyut Sriramakrishnan', 'gender': 'Male', 'doctor': doctors[1]},
            {'patient_id': 'PED003', 'full_name': 'Swastika', 'gender': 'Female', 'doctor': doctors[2]},
        ]
        
        patients = []
        for patient_data in patients_data:
            patient, created = Patient.objects.get_or_create(
                patient_id=patient_data['patient_id'],
                defaults={
                    'full_name': patient_data['full_name'],
                    'gender': patient_data['gender'],
                    'doctor': patient_data['doctor'],
                    'created_at': timezone.now().replace(year=2025, month=4, day=28)
                }
            )
            patients.append(patient)
            self.stdout.write(f"{'Created' if created else 'Got'} patient: {patient.full_name}")
        
        # Create chapters and words matching the admin interface
        phoneme_data = [
            {
                'chapter_number': 1,
                'name': 'P Sound',
                'words': ["pen", "apple", "stop", "people", "pepper", 
                         "puppy", "paper", "purple", "spoon", "spot", 
                         "speak", "jump", "lamp", "tape", "help"]
            },
            {
                'chapter_number': 2,
                'name': 'B Sound',
                'words': ["ball", "baby", "book", "bird", "boat", 
                         "box", "blue", "bread", "bear", "rabbit", 
                         "table", "rubber", "bubble", "grab", "crab"]
            },
            {
                'chapter_number': 3,
                'name': 'T Sound',
                'words': ["time", "water", "cat", "tiger", "tree", 
                         "train", "top", "butter", "letter", "bottle", 
                         "turtle", "teacher", "today", "twenty", "star"]
            },
            {
                'chapter_number': 4,
                'name': 'D Sound',
                'words': ["dog", "red", "bed", "door", "day", 
                         "duck", "desk", "daddy", "dinner", "under", 
                         "ladder", "candy", "bird", "hand", "land"]
            },
            {
                'chapter_number': 5,
                'name': 'K Sound',
                'words': ["cat", "book", "duck", "key", "cake", 
                         "car", "cookie", "kite", "king", "sock", 
                         "back", "chicken", "truck", "black", "clock"]
            }
        ]
        
        # Create chapters and words
        for chapter_data in phoneme_data:
            chapter, created = Chapter.objects.get_or_create(
                chapter_number=chapter_data['chapter_number'],
                defaults={'name': chapter_data['name']}
            )
            self.stdout.write(f"{'Created' if created else 'Got'} chapter: {chapter.name}")
            
            for order, word_text in enumerate(chapter_data['words'], start=1):
                word, created = Word.objects.get_or_create(
                    chapter=chapter,
                    word=word_text,
                    defaults={'order': order}
                )
                if created:
                    self.stdout.write(f"Created word: {word_text}")
        
        # Create progress data for each patient
        for patient in patients:
            # Create progress for different chapters and words
            for chapter in Chapter.objects.all()[:3]:  # First 3 chapters
                for word in chapter.words.all()[:10]:  # First 10 words per chapter
                    # Create 3-5 trials per word with increasing accuracy
                    num_trials = random.randint(3, 5)
                    for i in range(num_trials):
                        progress_date = timezone.now().date() - timedelta(days=random.randint(1, 30))
                        progress_time = time(hour=random.randint(9, 16), minute=random.randint(0, 59))
                        base_accuracy = random.randint(60, 70)
                        
                        progress, created = Progress.objects.get_or_create(
                            patient=patient,
                            word=word,
                            trial_number=i+1,
                            date=progress_date,
                            defaults={
                                'accuracy': base_accuracy + i*5,  # Increasing accuracy
                                'time': progress_time
                            }
                        )
                        if created:
                            self.stdout.write(f"Created progress for {patient.full_name} - {word.word} - Trial {i+1}")
        
        # Create session history for each patient
        for patient in patients:
            # Create 10-15 session history entries
            for i in range(random.randint(10, 15)):
                session_date = timezone.now().date() - timedelta(days=i*2)
                
                # Format duration as minutes string
                duration_minutes = random.randint(30, 60)
                duration_str = f"{duration_minutes} min"
                
                session, created = SessionHistory.objects.get_or_create(
                    patient=patient,
                    date=session_date,
                    defaults={
                        'duration': duration_str,
                        'score': random.randint(75, 95),
                    }
                )
                if created:
                    self.stdout.write(f"Created session history for {patient.full_name} on {session_date}")
        
        self.stdout.write(self.style.SUCCESS('Successfully populated sample data'))