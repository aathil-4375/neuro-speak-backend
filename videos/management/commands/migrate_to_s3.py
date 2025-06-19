from django.core.management.base import BaseCommand
from videos.models import Video
import os
from django.conf import settings
import shutil

class Command(BaseCommand):
    help = 'Migrate local video files to S3'

    def handle(self, *args, **options):
        videos = Video.objects.all()
        
        for video in videos:
            if video.video_file:
                old_path = video.video_file.path if hasattr(video.video_file, 'path') else None
                old_url = video.video_file.url
                
                self.stdout.write(f"Processing: {video.title}")
                self.stdout.write(f"Current URL: {old_url}")
                
                # If file is local (not S3), re-save to trigger S3 upload
                if old_path and os.path.exists(old_path):
                    # Open the local file
                    with open(old_path, 'rb') as f:
                        # Re-save the file (this will upload to S3)
                        video.video_file.save(
                            os.path.basename(old_path),
                            f,
                            save=True
                        )
                    
                    self.stdout.write(
                        self.style.SUCCESS(f"✅ Migrated {video.title} to S3")
                    )
                    self.stdout.write(f"New URL: {video.video_file.url}")
                else:
                    self.stdout.write(
                        self.style.WARNING(f"⚠️ Local file not found for {video.title}")
                    )
                
                print("---")