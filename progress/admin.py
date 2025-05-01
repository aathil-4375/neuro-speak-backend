# backend/progress/admin.py
from django.contrib import admin
from .models import Progress, SessionHistory
from chapters.models import Word

@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    list_display = ('patient', 'word', 'trial_number', 'accuracy', 'date', 'time')
    list_filter = ('patient', 'word__chapter', 'date')
    search_fields = ('patient__full_name', 'word__word')
    ordering = ('-date', '-time')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "word":
            # This makes sure words are grouped by chapter in dropdown
            kwargs["queryset"] = Word.objects.select_related('chapter').order_by('chapter__chapter_number', 'order')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(SessionHistory)
class SessionHistoryAdmin(admin.ModelAdmin):
    list_display = ('patient', 'date', 'duration', 'score')
    list_filter = ('patient', 'date')
    search_fields = ('patient__full_name',)
    ordering = ('-date',)