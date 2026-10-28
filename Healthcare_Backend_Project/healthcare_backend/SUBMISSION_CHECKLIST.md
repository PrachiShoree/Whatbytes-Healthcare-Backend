# Assignment Requirement Checklist

This checklist maps the supplied assignment to the implementation.

- [x] Django project structure (`config/`, `healthcare/`, `manage.py`)
- [x] Django REST Framework for REST APIs
- [x] PostgreSQL database configuration via environment variables
- [x] JWT authentication with `djangorestframework-simplejwt`
- [x] Registration with name, email, password; email-based login returns access and refresh JWTs
- [x] Django ORM models for users, patients, doctors, and patient-doctor mappings
- [x] Patient create/list/detail/update/delete APIs; lists and details are scoped to the authenticated owner
- [x] Doctor create/list/detail/update/delete APIs; authenticated users can list/view, creator-only mutations
- [x] Mapping create/list/get-by-patient/delete APIs
- [x] Input validation (email, password, age, gender, phone, experience, duplicate mappings)
- [x] JSON error responses and appropriate HTTP status codes
- [x] Environment-based sensitive configuration (`.env.example`; real `.env` excluded)
- [x] Database initial migration included
- [x] Automated API tests included
- [x] Postman collection included
- [x] Setup/run instructions included in `README.md`
- [x] Docker Compose PostgreSQL and app services included

## Before submitting

1. Replace the development values in `.env` with your own local secret/database credentials.
2. Run migrations and `python manage.py check`.
3. Run `python manage.py test healthcare`.
4. Start the server and import the Postman collection to test each endpoint.
5. Take screenshots of successful registration/login, patient CRUD, doctor CRUD, and mapping operations if your instructor asks for evidence.
6. Never submit a real `.env` file or real patient data.
