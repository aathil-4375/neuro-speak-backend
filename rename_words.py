#!/usr/bin/env python
"""
Word Renaming Script
This script helps you rename existing words in the database.
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

from chapters.models import Chapter, Word

def rename_words():
    """
    Rename words in the database.
    """
    print("📝 Word Renaming Tool")
    print("=" * 40)
    
    # Show existing words
    chapters = Chapter.objects.all().order_by('chapter_number')
    
    if not chapters.exists():
        print("❌ No chapters found in database")
        return
    
    print("\n📚 Current Words in Database:")
    print("-" * 40)
    
    for chapter in chapters:
        print(f"\n📖 {chapter.name}:")
        words = Word.objects.filter(chapter=chapter).order_by('order')
        
        if not words.exists():
            print("  (No words found)")
            continue
            
        for word in words:
            print(f"  {word.order}. {word.word}")
    
    print("\n🔄 Renaming Options:")
    print("1. Rename individual words")
    print("2. Bulk rename from file")
    print("3. Exit")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == '1':
        rename_individual_words()
    elif choice == '2':
        bulk_rename_from_file()
    elif choice == '3':
        print("👋 Goodbye!")
    else:
        print("❌ Invalid choice")

def rename_individual_words():
    """
    Rename words one by one.
    """
    print("\n🔄 Individual Word Renaming")
    print("-" * 30)
    
    while True:
        # Show current words
        chapters = Chapter.objects.all().order_by('chapter_number')
        
        print("\n📚 Current Words:")
        for chapter in chapters:
            print(f"\n📖 {chapter.name}:")
            words = Word.objects.filter(chapter=chapter).order_by('order')
            for word in words:
                print(f"  {word.id}. {word.word}")
        
        # Get word to rename
        try:
            word_id = input("\nEnter word ID to rename (or 'quit' to exit): ").strip()
            
            if word_id.lower() == 'quit':
                break
                
            word_id = int(word_id)
            word = Word.objects.get(id=word_id)
            
            print(f"\nCurrent word: {word.word}")
            new_name = input("Enter new name: ").strip()
            
            if new_name:
                old_name = word.word
                word.word = new_name
                word.save()
                print(f"✅ Renamed '{old_name}' to '{new_name}'")
            else:
                print("❌ New name cannot be empty")
                
        except ValueError:
            print("❌ Please enter a valid number")
        except Word.DoesNotExist:
            print("❌ Word not found")
        except Exception as e:
            print(f"❌ Error: {e}")

def bulk_rename_from_file():
    """
    Bulk rename words from a text file.
    """
    print("\n📄 Bulk Rename from File")
    print("-" * 30)
    
    file_path = input("Enter the path to your rename file: ").strip()
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        renamed_count = 0
        errors = []
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            # Expected format: word_id|new_name
            if '|' in line:
                parts = line.split('|', 1)
                if len(parts) == 2:
                    word_id_str, new_name = parts
                    
                    try:
                        word_id = int(word_id_str.strip())
                        new_name = new_name.strip()
                        
                        if new_name:
                            word = Word.objects.get(id=word_id)
                            old_name = word.word
                            word.word = new_name
                            word.save()
                            print(f"✅ Line {line_num}: Renamed '{old_name}' to '{new_name}'")
                            renamed_count += 1
                        else:
                            errors.append(f"Line {line_num}: Empty new name")
                            
                    except ValueError:
                        errors.append(f"Line {line_num}: Invalid word ID '{word_id_str}'")
                    except Word.DoesNotExist:
                        errors.append(f"Line {line_num}: Word ID {word_id_str} not found")
                    except Exception as e:
                        errors.append(f"Line {line_num}: Error - {e}")
                else:
                    errors.append(f"Line {line_num}: Invalid format, expected 'word_id|new_name'")
            else:
                errors.append(f"Line {line_num}: Invalid format, expected 'word_id|new_name'")
        
        print(f"\n📊 Bulk Rename Summary:")
        print(f"✅ Renamed: {renamed_count} words")
        print(f"❌ Errors: {len(errors)}")
        
        if errors:
            print("\n❌ Errors:")
            for error in errors:
                print(f"  - {error}")
                
    except Exception as e:
        print(f"❌ Error reading file: {e}")

def create_rename_template():
    """
    Create a template file for bulk renaming.
    """
    print("\n📄 Creating Rename Template")
    print("-" * 30)
    
    template_content = """# Word Rename Template
# Format: word_id|new_name
# Example: 1|அம்மா
# Lines starting with # are ignored

# Chapter 1 Words
1|அம்மா
2|அப்பா
3|நண்பன்

# Chapter 2 Words
4|பள்ளி
5|வீடு
6|கார்

# Add more words as needed
"""
    
    template_file = "word_rename_template.txt"
    
    try:
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        print(f"✅ Template created: {template_file}")
        print("📝 Edit this file with your word mappings, then use bulk rename")
        
    except Exception as e:
        print(f"❌ Error creating template: {e}")

if __name__ == '__main__':
    print("📝 Word Renaming Tool")
    print("=" * 40)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--template':
            create_rename_template()
        else:
            print(f"Unknown option: {sys.argv[1]}")
            print("Available options: --template")
    else:
        rename_words() 