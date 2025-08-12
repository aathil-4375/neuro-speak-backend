from django.core.management.base import BaseCommand
from django.core.files import File
from pathlib import Path
from videos.models import VideoUpload
from chapters.models import Chapter, Word
from patients.models import Patient

class Command(BaseCommand):
    help = 'Upload reference videos for all words in chapters'

    def add_arguments(self, parser):
        parser.add_argument(
            '--videos-dir',
            type=str,
            default='reference_videos',
            help='Directory containing video files'
        )
        parser.add_argument(
            '--patient-id',
            type=str,
            default='REF001',
            help='Patient ID for reference videos'
        )
        parser.add_argument(
            '--doctor-id',
            type=int,
            default=1,
            help='Doctor ID for the patient'
        )

    def handle(self, *args, **options):
        videos_dir = Path(options['videos_dir'])
        patient_id = options['patient_id']
        doctor_id = options['doctor_id']

        if not videos_dir.exists():
            self.stdout.write(
                self.style.ERROR(f'❌ Videos directory not found: {videos_dir}')
            )
            self.stdout.write(
                self.style.WARNING('Please create the directory and add your video files.')
            )
            return

        # Get or create default patient
        try:
            default_patient, created = Patient.objects.get_or_create(
                patient_id=patient_id,
                defaults={
                    'full_name': 'Reference Videos',
                    'gender': 'Other',
                    'doctor_id': doctor_id,
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Created default patient: {default_patient.full_name}')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error creating patient: {e}')
            )
            return

        uploaded_count = 0
        skipped_count = 0

        # Process each chapter directory
        for chapter_dir in videos_dir.iterdir():
            if not chapter_dir.is_dir():
                continue

            # Extract chapter number
            try:
                chapter_number = int(chapter_dir.name.split('_')[1])
            except (IndexError, ValueError):
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Skipping invalid chapter directory: {chapter_dir.name}')
                )
                continue

            # Get or create chapter
            chapter, created = Chapter.objects.get_or_create(
                chapter_number=chapter_number,
                defaults={'name': f'Chapter {chapter_number}'}
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Created chapter: {chapter.name}')
                )

            # Process video files
            for video_file in chapter_dir.glob('*.mp4'):
                filename = video_file.stem

                try:
                    # Parse filename: word_1_tamil.mp4
                    parts = filename.split('_')
                    if len(parts) >= 3:
                        word_number = int(parts[1])
                        language = parts[2].lower()

                        if language not in ['tamil', 'sinhala']:
                            self.stdout.write(
                                self.style.WARNING(f'⚠️  Invalid language in filename: {filename}')
                            )
                            continue

                        # Get or create word
                        word, created = Word.objects.get_or_create(
                            chapter=chapter,
                            word=f'Word {word_number}',
                            defaults={'order': word_number}
                        )

                        if created:
                            self.stdout.write(
                                self.style.SUCCESS(f'✅ Created word: {word.word} in {chapter.name}')
                            )

                        # Check if video already exists
                        existing_video = VideoUpload.objects.filter(
                            patient=default_patient,
                            chapter=chapter,
                            word=word,
                            language=language,
                            video_type='reference'
                        ).first()

                        if existing_video:
                            self.stdout.write(
                                self.style.WARNING(f'⏭️  Skipping existing video: {filename}')
                            )
                            skipped_count += 1
                            continue

                        # Create video upload (reference videos don't have patients)
                        with open(video_file, 'rb') as f:
                            video_upload = VideoUpload(
                                patient=None,  # Reference videos are not associated with any patient
                                chapter=chapter,
                                word=word,
                                language=language,
                                video_type='reference',
                                trial_number=1,
                                is_approved=True
                            )
                            video_upload.video_file.save(
                                video_file.name,
                                File(f),
                                save=True
                            )

                        self.stdout.write(
                            self.style.SUCCESS(f'✅ Uploaded: {filename}')
                        )
                        uploaded_count += 1

                    else:
                        self.stdout.write(
                            self.style.WARNING(f'⚠️  Invalid filename format: {filename}')
                        )

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Error processing {filename}: {e}')
                    )

        # Summary
        self.stdout.write(
            self.style.SUCCESS(f'\n📊 Upload Summary:')
        )
        self.stdout.write(
            self.style.SUCCESS(f'✅ Uploaded: {uploaded_count} videos')
        )
        self.stdout.write(
            self.style.WARNING(f'⏭️  Skipped: {skipped_count} videos (already exist)')
        )
        self.stdout.write(
            self.style.SUCCESS(f'📁 Total processed: {uploaded_count + skipped_count}')
        ) 