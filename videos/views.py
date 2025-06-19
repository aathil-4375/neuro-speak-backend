from rest_framework import status, generics
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.http import JsonResponse, HttpResponse
import os
from django.conf import settings
from .models import Video
from .serializers import VideoSerializer, VideoUploadSerializer

class VideoUploadView(generics.CreateAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoUploadSerializer
    parser_classes = (MultiPartParser, FormParser)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            video = serializer.save()
            response_serializer = VideoSerializer(video)
            return Response({
                'message': 'Video uploaded successfully!',
                'video': response_serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([AllowAny])
def test_video_upload(request):
    """
    Test endpoint to verify video upload is working locally.
    Returns a simple HTML form for testing file uploads.
    """
    html = """
    <!DOCTYPE html>
    <html>
    <body>
        <h2>Test Video Upload</h2>
        <p>Use this form to test video uploads to local storage</p>
        
        <form action="/api/videos/upload/" method="post" enctype="multipart/form-data">
            <div>
                <label for="title">Title:</label><br>
                <input type="text" id="title" name="title" value="Test Video">
            </div>
            <div style="margin: 15px 0;">
                <label for="video_file">Video File:</label><br>
                <input type="file" id="video_file" name="video_file" accept="video/*">
            </div>
            <div>
                <button type="submit">Upload Video</button>
            </div>
        </form>
        
        <div style="margin-top: 30px;">
            <h3>Uploaded Videos</h3>
            <a href="/api/videos/" target="_blank">View All Videos (API)</a>
        </div>
    </body>
    </html>
    """
    return HttpResponse(html)

class VideoListView(generics.ListAPIView):
    queryset = Video.objects.all().order_by('-uploaded_at')
    serializer_class = VideoSerializer

class VideoDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer

# Simple function-based view (easier to understand)
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def upload_video_simple(request):
    """Simple video upload endpoint"""
    if request.method == 'POST':
        print("Received upload request")  # Debug
        print("Files:", request.FILES)     # Debug
        print("Data:", request.data)       # Debug
        
        serializer = VideoUploadSerializer(data=request.data)
        if serializer.is_valid():
            video = serializer.save()
            response_data = VideoSerializer(video).data
            return Response({
                'success': True,
                'message': 'Video uploaded successfully to AWS S3!',
                'video': response_data
            }, status=status.HTTP_201_CREATED)
        else:
            print("Serializer errors:", serializer.errors)  # Debug
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)