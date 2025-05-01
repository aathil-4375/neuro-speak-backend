# backend/chapters/serializers.py
from rest_framework import serializers
from .models import Chapter, Word

class WordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Word
        fields = ['id', 'word', 'order', 'chapter']

class ChapterSerializer(serializers.ModelSerializer):
    words = WordSerializer(many=True, read_only=True)
    
    class Meta:
        model = Chapter
        fields = ['id', 'chapter_number', 'name', 'words']