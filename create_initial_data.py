# create_initial_data.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from chapters.models import Chapter, Word

# Create chapters
chapters_data = [
    {"chapter_number": 1, "name": "Chapter 01"},
    {"chapter_number": 2, "name": "Chapter 02"},
    {"chapter_number": 3, "name": "Chapter 03"},
    {"chapter_number": 4, "name": "Chapter 04"},
    {"chapter_number": 5, "name": "Chapter 05"},
    {"chapter_number": 6, "name": "Chapter 06"},
    {"chapter_number": 7, "name": "Chapter 07"},
    {"chapter_number": 8, "name": "Chapter 08"},
    {"chapter_number": 9, "name": "Chapter 09"},
    {"chapter_number": 10, "name": "Chapter 10"},
]

# Create words for each chapter
words_data = [
    "word1", "word2", "word3", "word4", "word5",
    "word6", "word7", "word8", "word9", "word10",
    "word11", "word12", "word13", "word14", "word15"
]

for chapter_data in chapters_data:
    chapter, created = Chapter.objects.get_or_create(
        chapter_number=chapter_data["chapter_number"],
        defaults={"name": chapter_data["name"]}
    )
    
    if created:
        print(f"Created {chapter.name}")
        
        # Create words for this chapter
        for index, word in enumerate(words_data, start=1):
            Word.objects.create(
                chapter=chapter,
                word=word,
                order=index
            )
        print(f"Added {len(words_data)} words to {chapter.name}")

print("Initial data creation complete!")