from django.db import IntegrityError, transaction
from django.http import JsonResponse
from rest_framework import generics, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import Patient, Doctor, PatientDoctorMapping
from .serializers import RegisterSerializer, LoginSerializer, PatientSerializer, DoctorSerializer, PatientDoctorMappingSerializer
from .permissions import IsDoctorCreatorOrReadOnly

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({"message": "Registration successful.", "user": {"id": user.id, "name": user.get_full_name().strip(), "email": user.email}}, status=status.HTTP_201_CREATED)

class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

@api_view(["GET"])
@permission_classes([AllowAny])
def api_root(request):
    return Response({
        "message": "Healthcare Backend API",
        "authentication": {"register": "/api/auth/register/", "login": "/api/auth/login/", "refresh": "/api/auth/token/refresh/"},
        "patients": "/api/patients/", "doctors": "/api/doctors/", "mappings": "/api/mappings/",
        "documentation": "See README.md and postman/Healthcare_Backend.postman_collection.json.",
    })

class PatientViewSet(viewsets.ModelViewSet):
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Patient.objects.filter(user=self.request.user).select_related("user")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class DoctorViewSet(viewsets.ModelViewSet):
    serializer_class = DoctorSerializer
    permission_classes = [IsAuthenticated, IsDoctorCreatorOrReadOnly]
    queryset = Doctor.objects.select_related("created_by").all()
    filterset_fields = ["specialization"]
    search_fields = ["full_name", "specialization", "qualifications"]
    ordering_fields = ["full_name", "experience_years", "created_at"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class MappingViewSet(viewsets.ModelViewSet):
    serializer_class = PatientDoctorMappingSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_queryset(self):
        queryset = PatientDoctorMapping.objects.filter(patient__user=self.request.user).select_related("patient", "doctor", "assigned_by")
        patient_id = self.request.query_params.get("patient_id")
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                self.perform_create(serializer)
        except IntegrityError:
            return Response({"detail": "This doctor is already assigned to this patient."}, status=status.HTTP_400_BAD_REQUEST)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save(assigned_by=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        # The assignment's GET /api/mappings/<patient_id>/ means list mappings for that patient.
        patient_id = kwargs.get("pk")
        if not Patient.objects.filter(pk=patient_id, user=request.user).exists():
            return Response({"detail": "Patient not found."}, status=status.HTTP_404_NOT_FOUND)
        items = self.get_queryset().filter(patient_id=patient_id)
        return Response(self.get_serializer(items, many=True).data)

    def update(self, request, *args, **kwargs):
        return Response({"detail": "Updating a mapping is not supported. Delete it and create a new mapping."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def partial_update(self, request, *args, **kwargs):
        return Response({"detail": "Updating a mapping is not supported. Delete it and create a new mapping."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
