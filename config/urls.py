# config/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),
    path('api/patients/', include('patients.urls')),
    path('api/chapters/', include('chapters.urls')),
    path('api/progress/', include('progress.urls')),
]