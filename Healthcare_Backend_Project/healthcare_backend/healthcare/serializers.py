from django.contrib.auth import authenticate, password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User, Patient, Doctor, PatientDoctorMapping

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, trim_whitespace=False, style={"input_type": "password"})
    name = serializers.CharField(write_only=True, max_length=301, required=False)

    class Meta:
        model = User
        fields = ["id", "name", "first_name", "last_name", "email", "password"]
        read_only_fields = ["id"]
        extra_kwargs = {"first_name": {"required": False}, "last_name": {"required": False}, "email": {"required": True}}

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate(self, attrs):
        name = attrs.pop("name", "").strip()
        if name and not attrs.get("first_name"):
            parts = name.split(maxsplit=1)
            attrs["first_name"] = parts[0]
            attrs["last_name"] = parts[1] if len(parts) > 1 else ""
        if not attrs.get("first_name", "").strip():
            raise serializers.ValidationError({"name": "Provide name or first_name."})
        attrs["first_name"] = attrs["first_name"].strip()
        attrs["last_name"] = attrs.get("last_name", "").strip()
        candidate = User(email=attrs.get("email", ""), first_name=attrs["first_name"], last_name=attrs["last_name"])
        try:
            password_validation.validate_password(attrs["password"], user=candidate)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        return User.objects.create_user(password=password, **validated_data)

class LoginSerializer(TokenObtainPairSerializer):
    username_field = User.EMAIL_FIELD

    def validate(self, attrs):
        email = attrs.get("email", "").strip().lower()
        password = attrs.get("password", "")
        user = authenticate(request=self.context.get("request"), email=email, password=password)
        if not user:
            raise serializers.ValidationError({"detail": "Invalid email or password."})
        if not user.is_active:
            raise serializers.ValidationError({"detail": "This account is inactive."})
        refresh = self.get_token(user)
        return {"refresh": str(refresh), "access": str(refresh.access_token), "user": {"id": user.id, "name": user.get_full_name().strip(), "email": user.email}}

class PatientSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = Patient
        fields = ["id", "user", "full_name", "age", "gender", "phone", "email", "address", "medical_history", "created_at", "updated_at"]
        read_only_fields = ["id", "user", "created_at", "updated_at"]

class DoctorSerializer(serializers.ModelSerializer):
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = Doctor
        fields = ["id", "created_by", "full_name", "specialization", "email", "phone", "qualifications", "experience_years", "created_at", "updated_at"]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]

class PatientDoctorMappingSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    doctor_name = serializers.CharField(source="doctor.full_name", read_only=True)
    patient = serializers.PrimaryKeyRelatedField(queryset=Patient.objects.all())
    doctor = serializers.PrimaryKeyRelatedField(queryset=Doctor.objects.all())

    class Meta:
        model = PatientDoctorMapping
        fields = ["id", "patient", "patient_name", "doctor", "doctor_name", "assigned_by", "assigned_at"]
        read_only_fields = ["id", "assigned_by", "assigned_at", "patient_name", "doctor_name"]

    def validate_patient(self, value):
        request = self.context.get("request")
        if request and value.user_id != request.user.id:
            raise serializers.ValidationError("You can only assign doctors to patients you created.")
        return value

    def validate(self, attrs):
        patient = attrs.get("patient", getattr(self.instance, "patient", None))
        doctor = attrs.get("doctor", getattr(self.instance, "doctor", None))
        if patient and doctor and PatientDoctorMapping.objects.filter(patient=patient, doctor=doctor).exclude(pk=getattr(self.instance, "pk", None)).exists():
            raise serializers.ValidationError({"doctor": "This doctor is already assigned to this patient."})
        return attrs
