# backend/chapters/admin.py
from django.contrib import admin
from .models import Chapter, Word

class WordInline(admin.TabularInline):
    model = Word
    extra = 1
    fields = ['word', 'order']
    ordering = ['order']

@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ('chapter_number', 'name')
    search_fields = ('name',)
    ordering = ('chapter_number',)
    inlines = [WordInline]

@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    list_display = ('word', 'chapter', 'order')
    list_filter = ('chapter',)
    search_fields = ('word',)
    ordering = ('chapter', 'order')