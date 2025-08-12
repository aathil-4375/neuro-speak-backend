# videos/models.py
from django.db import models
from django.conf import settings
from patients.models import Patient
from chapters.models import Chapter, Word

class VideoUpload(models.Model):
    LANGUAGE_CHOICES = [
        ('tamil', 'Tamil'),
        ('sinhala', 'Sinhala'),
    ]
    
    VIDEO_TYPE_CHOICES = [
        ('reference', 'Reference Video'),
        ('patient_trial', 'Patient Trial Video'),
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='videos', null=True, blank=True)
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='videos')
    word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name='videos')
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES)
    video_type = models.CharField(max_length=15, choices=VIDEO_TYPE_CHOICES)
    video_file = models.FileField(upload_to='videos/')
    s3_key = models.CharField(max_length=500, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    trial_number = models.IntegerField(default=1)
    accuracy_score = models.FloatField(null=True, blank=True)
    duration = models.FloatField(null=True, blank=True)  # in seconds
    is_approved = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-uploaded_at']
        # Reference videos are unique per word+language (no patient)
        # Patient trial videos are unique per patient+word+language+trial
        unique_together = [
            ('chapter', 'word', 'language', 'video_type'),  # For reference videos
            ('patient', 'chapter', 'word', 'language', 'trial_number')  # For patient trials
        ]
    
    def __str__(self):
        if self.video_type == 'reference':
            return f"Reference - {self.chapter.name} - {self.word.word} - {self.language}"
        else:
            return f"{self.patient.patient_id} - {self.chapter.name} - {self.word.word} - {self.language} - Trial {self.trial_number}"
    
    def get_s3_path(self):
        """Generate S3 path based on video type"""
        if self.video_type == 'reference':
            # Reference videos: reference/chapter/word/language.mp4
            return f"reference/{self.chapter.chapter_number}/{self.word.word}/"
        else:
            # Patient videos: patient/class/word/
            return f"{self.patient.patient_id}/{self.chapter.chapter_number}/{self.word.word}/"
    
    def save(self, *args, **kwargs):
        if not self.s3_key:
            if self.video_type == 'reference':
                self.s3_key = f"{self.get_s3_path()}{self.language}_reference.mp4"
            else:
                self.s3_key = f"{self.get_s3_path()}{self.language}_patient_trial_{self.trial_number}.mp4"
        super().save(*args, **kwargs)
    
    def clean(self):
        """Validate that reference videos don't have patients"""
        if self.video_type == 'reference' and self.patient:
            raise ValidationError("Reference videos should not be associated with a specific patient")
        if self.video_type == 'patient_trial' and not self.patient:
            raise ValidationError("Patient trial videos must be associated with a patient")

class VideoProgress(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='video_progress')
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='video_progress')
    word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name='video_progress')
    language = models.CharField(max_length=10, choices=VideoUpload.LANGUAGE_CHOICES)
    current_trial = models.IntegerField(default=1)
    best_accuracy = models.FloatField(default=0.0)
    completed = models.BooleanField(default=False)
    last_attempt = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['patient', 'chapter', 'word', 'language']
    
    def __str__(self):
        return f"{self.patient.patient_id} - {self.chapter.name} - {self.word.word} - {self.language}" 