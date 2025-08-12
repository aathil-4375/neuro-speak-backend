#!/usr/bin/env python
"""
Bulk Upload Reference Videos Script
This script helps you upload reference videos for all words in chapters.
Supports separate Tamil and Sinhala word sets with organized folder structure.
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from videos.models import VideoUpload
from chapters.models import Chapter, Word
from django.core.files import File

def upload_reference_videos():
    """
    Upload reference videos for all words in chapters.
    Video files should be organized in the following structure:
    
    reference_videos/
    ├── tamil/
    │   ├── chapter_1/
    │   │   ├── அம்மா.mp4              # Tamil word
    │   │   ├── அப்பா.mp4              # Tamil word
    │   │   └── என்ன_அவசரம்.mp4       # Tamil word
    │   └── chapter_2/
    │       └── ...
    ├── sinhala/
    │   ├── chapter_1/
    │   │   ├── අම්මා.mp4              # Sinhala word
    │   │   ├── තාත්තා.mp4             # Sinhala word
    │   │   └── මොකද_ඉක්මනින්.mp4     # Sinhala word
    │   └── chapter_2/
    │       └── ...
    """
    
    # Base directory for video files
    videos_dir = BASE_DIR / 'reference_videos'
    
    if not videos_dir.exists():
        print(f"❌ Videos directory not found: {videos_dir}")
        print("Please create the directory and add your video files.")
        print("\n📁 Expected structure:")
        print("reference_videos/")
        print("├── tamil/")
        print("│   ├── chapter_1/")
        print("│   │   ├── அம்மா.mp4")
        print("│   │   └── அப்பா.mp4")
        print("│   └── chapter_2/")
        print("├── sinhala/")
        print("│   ├── chapter_1/")
        print("│   │   ├── අම්මා.mp4")
        print("│   │   └── තාත්තා.mp4")
        print("│   └── chapter_2/")
        return
    
    uploaded_count = 0
    skipped_count = 0
    words_created = 0
    
    # Process each language directory
    for language_dir in videos_dir.iterdir():
        if not language_dir.is_dir():
            continue
            
        language = language_dir.name.lower()
        
        # Validate language
        if language not in ['tamil', 'sinhala']:
            print(f"⚠️  Skipping invalid language directory: {language_dir.name}")
            continue
        
        print(f"\n🌍 Processing {language.capitalize()} videos...")
        
        # Process each chapter directory within the language
        for chapter_dir in language_dir.iterdir():
            if not chapter_dir.is_dir():
                continue
                
            # Extract chapter number from directory name (e.g., "chapter_1" -> 1)
            try:
                chapter_number = int(chapter_dir.name.split('_')[1])
            except (IndexError, ValueError):
                print(f"⚠️  Skipping invalid chapter directory: {chapter_dir.name}")
                continue
            
            # Get or create chapter
            chapter, created = Chapter.objects.get_or_create(
                chapter_number=chapter_number,
                defaults={'name': f'Chapter {chapter_number}'}
            )
            
            if created:
                print(f"✅ Created chapter: {chapter.name}")
            
            # Process video files in chapter directory
            for video_file in chapter_dir.glob('*.mp4'):
                filename = video_file.stem  # Remove .mp4 extension
                
                if not filename:
                    print(f"⚠️  Skipping empty filename: {video_file.name}")
                    continue
                
                print(f"\n📝 Processing word: {filename} ({language})")
                
                # Get or create word with actual name
                word, created = Word.objects.get_or_create(
                    chapter=chapter,
                    word=filename,
                    defaults={'order': len(list(chapter_dir.glob('*.mp4')))}  # Use order based on number of files
                )
                
                if created:
                    print(f"✅ Created word: '{filename}' in {chapter.name}")
                    words_created += 1
                
                # Check if reference video already exists
                existing_video = VideoUpload.objects.filter(
                    chapter=chapter,
                    word=word,
                    language=language,
                    video_type='reference'
                ).first()
                
                if existing_video:
                    print(f"⏭️  Skipping existing video: {filename} ({language})")
                    skipped_count += 1
                    continue
                
                # Create video upload (reference videos don't have patients)
                try:
                    with open(video_file, 'rb') as f:
                        video_upload = VideoUpload(
                            patient=None,  # Reference videos are global
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
                    
                    print(f"✅ Uploaded: {filename} ({language})")
                    uploaded_count += 1
                    
                except Exception as e:
                    print(f"❌ Error uploading {filename} ({language}): {e}")
    
    print(f"\n📊 Upload Summary:")
    print(f"✅ Uploaded: {uploaded_count} videos")
    print(f"⏭️  Skipped: {skipped_count} videos (already exist)")
    print(f"📝 Created: {words_created} new words")
    print(f"📁 Total processed: {uploaded_count + skipped_count}")

def list_video_structure():
    """
    List the expected video file structure.
    """
    print("📁 Expected Video File Structure:")
    print("reference_videos/")
    print("├── tamil/")
    print("│   ├── chapter_1/")
    print("│   │   ├── அம்மா.mp4              # Mother in Tamil")
    print("│   │   ├── அப்பா.mp4              # Father in Tamil")
    print("│   │   └── என்ன_அவசரம்.mp4       # What's the hurry in Tamil")
    print("│   ├── chapter_2/")
    print("│   │   ├── பள்ளி.mp4              # School in Tamil")
    print("│   │   └── வீடு.mp4               # House in Tamil")
    print("│   └── ...")
    print("├── sinhala/")
    print("│   ├── chapter_1/")
    print("│   │   ├── අම්මා.mp4              # Mother in Sinhala")
    print("│   │   ├── තාත්තා.mp4             # Father in Sinhala")
    print("│   │   └── මොකද_ඉක්මනින්.mp4     # What's the hurry in Sinhala")
    print("│   ├── chapter_2/")
    print("│   │   ├── පාසල.mp4              # School in Sinhala")
    print("│   │   └── ගෙදර.mp4               # House in Sinhala")
    print("│   └── ...")
    print("└── ...")
    print("\n📝 Naming Convention:")
    print("- Language directories: tamil/, sinhala/")
    print("- Chapter directories: chapter_1, chapter_2, etc.")
    print("- Video files: actual_word_name.mp4 (no language suffix needed)")
    print("- Examples: அம்மா.mp4, අම්මා.mp4")
    print("\n💡 Benefits:")
    print("- Separate word sets for Tamil and Sinhala")
    print("- Cleaner file organization")
    print("- No duplicate word names across languages")
    print("- Reference videos are global (same for all patients)")
    print("- Patient trial videos are individual per patient")

def show_existing_words():
    """
    Show existing words in the database grouped by language.
    """
    from chapters.models import Chapter, Word
    from videos.models import VideoUpload
    
    print("📚 Existing Words in Database:")
    print("=" * 50)
    
    chapters = Chapter.objects.all().order_by('chapter_number')
    for chapter in chapters:
        print(f"\n📖 {chapter.name}:")
        words = Word.objects.filter(chapter=chapter).order_by('order')
        
        if not words.exists():
            print("  (No words found)")
            continue
        
        for word in words:
            # Check which languages have videos for this word
            videos = VideoUpload.objects.filter(
                chapter=chapter,
                word=word,
                video_type='reference'
            )
            languages = [v.language for v in videos]
            
            if languages:
                print(f"  - {word.word} (Languages: {', '.join(languages)})")
            else:
                print(f"  - {word.word} (No videos)")

def create_directory_structure():
    """
    Create the recommended directory structure.
    """
    print("📁 Creating Directory Structure")
    print("-" * 30)
    
    videos_dir = BASE_DIR / 'reference_videos'
    
    # Create main directories
    directories = [
        videos_dir,
        videos_dir / 'tamil',
        videos_dir / 'sinhala',
    ]
    
    # Create chapter directories for both languages
    for language in ['tamil', 'sinhala']:
        for chapter_num in range(1, 6):  # Create chapters 1-5
            directories.append(videos_dir / language / f'chapter_{chapter_num}')
    
    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created: {directory}")
            created_count += 1
        else:
            print(f"⏭️  Exists: {directory}")
    
    print(f"\n📊 Directory Creation Summary:")
    print(f"✅ Created: {created_count} new directories")
    print(f"📁 Total directories: {len(directories)}")
    
    print(f"\n📝 Next Steps:")
    print("1. Add your Tamil videos to reference_videos/tamil/chapter_X/")
    print("2. Add your Sinhala videos to reference_videos/sinhala/chapter_X/")
    print("3. Run: python upload_reference_videos.py")

if __name__ == '__main__':
    print("🎥 Reference Video Upload Script")
    print("=" * 40)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--help':
            list_video_structure()
        elif sys.argv[1] == '--list-words':
            show_existing_words()
        elif sys.argv[1] == '--create-dirs':
            create_directory_structure()
        else:
            print(f"Unknown option: {sys.argv[1]}")
            print("Available options: --help, --list-words, --create-dirs")
    else:
        upload_reference_videos() 