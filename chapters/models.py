from django.db import models

class Chapter(models.Model):
    chapter_number = models.IntegerField(unique=True)
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return f"Chapter {self.chapter_number}"

class Word(models.Model):
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='words')
    word = models.CharField(max_length=100)
    order = models.IntegerField()
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return self.word