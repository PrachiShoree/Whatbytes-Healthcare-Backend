from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.db import models
from django.conf import settings

phone_validator = RegexValidator(
    regex=r"^\+?[0-9][0-9 ()-]{6,19}$",
    message="Enter a valid phone number (7–20 characters, digits and common phone symbols only).",
)

class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("An email address is required.")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True or extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_staff=True and is_superuser=True.")
        return self._create_user(email, password, **extra_fields)

class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150, blank=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name"]
    objects = UserManager()

    def __str__(self):
        return self.email

class Patient(models.Model):
    class Gender(models.TextChoices):
        MALE = "male", "Male"
        FEMALE = "female", "Female"
        OTHER = "other", "Other"
        PREFER_NOT_TO_SAY = "prefer_not_to_say", "Prefer not to say"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="patients")
    full_name = models.CharField(max_length=200)
    age = models.PositiveSmallIntegerField(validators=[MinValueValidator(0), MaxValueValidator(130)])
    gender = models.CharField(max_length=20, choices=Gender.choices)
    phone = models.CharField(max_length=25, validators=[phone_validator], blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    medical_history = models.TextField(blank=True, help_text="Optional; avoid entering information not needed for care.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "created_at"])]

    def __str__(self):
        return self.full_name

class Doctor(models.Model):
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="created_doctors")
    full_name = models.CharField(max_length=200)
    specialization = models.CharField(max_length=120)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=25, validators=[phone_validator], blank=True)
    qualifications = models.CharField(max_length=255, blank=True)
    experience_years = models.PositiveSmallIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(80)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["full_name"]

    def __str__(self):
        return f"Dr. {self.full_name} ({self.specialization})"

class PatientDoctorMapping(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="doctor_mappings")
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="patient_mappings")
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="created_mappings")
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-assigned_at"]
        constraints = [models.UniqueConstraint(fields=["patient", "doctor"], name="unique_patient_doctor_assignment")]

    def __str__(self):
        return f"{self.patient} → {self.doctor}"
