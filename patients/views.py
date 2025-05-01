# backend/patients/views.py
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Patient
from .serializers import PatientSerializer
import logging

logger = logging.getLogger(__name__)

class PatientListCreateView(generics.ListCreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = PatientSerializer
    
    def get_queryset(self):
        # Only return patients assigned to the current doctor
        return Patient.objects.filter(doctor=self.request.user)
    
    def create(self, request, *args, **kwargs):
        logger.info(f"Patient create request data: {request.data}")
        logger.info(f"User: {request.user}")
        
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Automatically assign the current user as the doctor
            patient = serializer.save(doctor=request.user)
            
            return Response(
                self.get_serializer(patient).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            logger.error(f"Error creating patient: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class PatientDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = PatientSerializer
    lookup_field = 'patient_id'
    
    def get_queryset(self):
        # Only allow access to patients assigned to the current doctor
        return Patient.objects.filter(doctor=self.request.user)

class PatientSearchView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    
    def get(self, request):
        query = request.query_params.get('query', '')
        if query:
            patients = Patient.objects.filter(
                doctor=request.user,
                patient_id__icontains=query
            )
            serializer = PatientSerializer(patients, many=True)
            return Response(serializer.data)
        return Response([])