#!/usr/bin/env python
"""
Fix Directory Structure Script
This script fixes the reference_videos directory structure.
"""

import os
import shutil
from pathlib import Path

def fix_directory_structure():
    """
    Fix the reference_videos directory structure.
    """
    print("🔧 Fixing Directory Structure")
    print("=" * 40)
    
    videos_dir = Path('reference_videos')
    
    if not videos_dir.exists():
        print("❌ reference_videos directory not found")
        return
    
    # Check for misplaced chapter directories
    misplaced_chapters = []
    for item in videos_dir.iterdir():
        if item.is_dir() and item.name.startswith('chapter_'):
            misplaced_chapters.append(item)
    
    if not misplaced_chapters:
        print("✅ Directory structure is already correct!")
        return
    
    print(f"🔍 Found {len(misplaced_chapters)} misplaced chapter directories:")
    for chapter in misplaced_chapters:
        print(f"  - {chapter.name}")
    
    # Create language directories if they don't exist
    tamil_dir = videos_dir / 'tamil'
    sinhala_dir = videos_dir / 'sinhala'
    
    tamil_dir.mkdir(exist_ok=True)
    sinhala_dir.mkdir(exist_ok=True)
    
    print(f"\n📁 Created language directories:")
    print(f"  - {tamil_dir}")
    print(f"  - {sinhala_dir}")
    
    # Move chapter directories to tamil folder (you can adjust this)
    moved_count = 0
    for chapter in misplaced_chapters:
        try:
            # Move to tamil folder (you can change this to sinhala if needed)
            new_path = tamil_dir / chapter.name
            if new_path.exists():
                print(f"⚠️  {chapter.name} already exists in tamil folder, skipping")
                continue
            
            shutil.move(str(chapter), str(new_path))
            print(f"✅ Moved {chapter.name} to tamil/")
            moved_count += 1
            
        except Exception as e:
            print(f"❌ Error moving {chapter.name}: {e}")
    
    print(f"\n📊 Summary:")
    print(f"✅ Moved: {moved_count} chapter directories")
    print(f"📁 Total processed: {len(misplaced_chapters)}")
    
    print(f"\n📝 Next Steps:")
    print("1. Check the moved directories in tamil/ folder")
    print("2. Move any Sinhala videos to sinhala/ folder manually if needed")
    print("3. Run: python upload_reference_videos.py")

def show_current_structure():
    """
    Show the current directory structure.
    """
    print("📁 Current Directory Structure:")
    print("=" * 40)
    
    videos_dir = Path('reference_videos')
    
    if not videos_dir.exists():
        print("❌ reference_videos directory not found")
        return
    
    def print_tree(path, prefix=""):
        items = sorted(path.iterdir())
        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            current_prefix = "└── " if is_last else "├── "
            next_prefix = "    " if is_last else "│   "
            
            print(f"{prefix}{current_prefix}{item.name}")
            
            if item.is_dir():
                print_tree(item, prefix + next_prefix)
    
    print_tree(videos_dir)

if __name__ == '__main__':
    print("🔧 Directory Structure Fix Tool")
    print("=" * 40)
    
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--show':
            show_current_structure()
        else:
            print(f"Unknown option: {sys.argv[1]}")
            print("Available options: --show")
    else:
        fix_directory_structure() 