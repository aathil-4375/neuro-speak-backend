from rest_framework import generics, permissions
from .models import Chapter, Word
from .serializers import ChapterSerializer, WordSerializer

class ChapterListView(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Chapter.objects.all()
    serializer_class = ChapterSerializer

class ChapterDetailView(generics.RetrieveAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Chapter.objects.all()
    serializer_class = ChapterSerializer
    lookup_field = 'chapter_number'

class WordListView(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = WordSerializer
    
    def get_queryset(self):
        chapter_number = self.kwargs['chapter_number']
        return Word.objects.filter(chapter__chapter_number=chapter_number)