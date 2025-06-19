from django.db import models
import uuid

def video_upload_path(instance, filename):
    """Generate unique filename for videos"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return f"videos/{filename}"

class Video(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    video_file = models.FileField(upload_to=video_upload_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_size = models.BigIntegerField(blank=True, null=True)
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if self.video_file and not self.file_size:
            self.file_size = self.video_file.size
        super().save(*args, **kwargs)