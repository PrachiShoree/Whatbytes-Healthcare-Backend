from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Patient, Doctor, PatientDoctorMapping

User = get_user_model()

@override_settings(REST_FRAMEWORK={
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework_simplejwt.authentication.JWTAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
})
class HealthcareAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="owner@example.com", password="StrongPass123!", first_name="Owner")
        self.other = User.objects.create_user(email="other@example.com", password="StrongPass123!", first_name="Other")
        response = self.client.post("/api/auth/login/", {"email": "owner@example.com", "password": "StrongPass123!"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

    def test_register_and_login(self):
        response = self.client.post("/api/auth/register/", {"name": "New User", "email": "new@example.com", "password": "AnotherStrong123!"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email="new@example.com").exists())
        response = self.client.post("/api/auth/login/", {"email": "new@example.com", "password": "AnotherStrong123!"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_patient_crud_and_owner_isolation(self):
        payload = {"full_name": "Aarav Sharma", "age": 35, "gender": "male", "phone": "+91 9876543210", "email": "aarav@example.com", "address": "Delhi"}
        response = self.client.post("/api/patients/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        patient_id = response.data["id"]
        self.assertEqual(self.client.get("/api/patients/").data["count"], 1)
        self.assertEqual(self.client.get(f"/api/patients/{patient_id}/").status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION="")
        other_token = self.client.post("/api/auth/login/", {"email": "other@example.com", "password": "StrongPass123!"}, format="json").data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {other_token}")
        self.assertEqual(self.client.get(f"/api/patients/{patient_id}/").status_code, status.HTTP_404_NOT_FOUND)

    def test_doctor_mapping_and_duplicate_validation(self):
        patient = Patient.objects.create(user=self.user, full_name="Mira Singh", age=28, gender="female")
        doctor = Doctor.objects.create(created_by=self.user, full_name="Aditi Rao", specialization="Cardiology", email="doctor@example.com")
        payload = {"patient": patient.id, "doctor": doctor.id}
        response = self.client.post("/api/mappings/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(self.client.get(f"/api/mappings/{patient.id}/").status_code, status.HTTP_200_OK)
        duplicate = self.client.post("/api/mappings/", payload, format="json")
        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(PatientDoctorMapping.objects.count(), 1)
        mapping_id = response.data["id"]
        self.assertEqual(self.client.delete(f"/api/mappings/{mapping_id}/").status_code, status.HTTP_204_NO_CONTENT)

    def test_unauthenticated_patient_access_is_denied(self):
        self.client.credentials(HTTP_AUTHORIZATION="")
        self.assertEqual(self.client.get("/api/patients/").status_code, status.HTTP_401_UNAUTHORIZED)
