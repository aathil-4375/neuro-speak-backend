from django.db import models
from patients.models import Patient
from chapters.models import Word

class Progress(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    word = models.ForeignKey(Word, on_delete=models.CASCADE)
    trial_number = models.IntegerField()
    accuracy = models.FloatField()
    date = models.DateField()
    time = models.TimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date', '-time']
    
    def __str__(self):
        return f"{self.patient.full_name} - {self.word.word} - Trial {self.trial_number}"

class SessionHistory(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    date = models.DateField()
    duration = models.CharField(max_length=20)
    score = models.FloatField()
    
    class Meta:
        ordering = ['-date']