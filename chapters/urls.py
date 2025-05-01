# chapters/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.ChapterListView.as_view(), name='chapter-list'),
    path('<int:chapter_number>/', views.ChapterDetailView.as_view(), name='chapter-detail'),
    path('<int:chapter_number>/words/', views.WordListView.as_view(), name='word-list'),
    
    # This endpoint is not needed anymore since we have the progress endpoint
    # path('<int:chapter_number>/data/', views.ChapterWordsView.as_view(), name='chapter-data'),
]