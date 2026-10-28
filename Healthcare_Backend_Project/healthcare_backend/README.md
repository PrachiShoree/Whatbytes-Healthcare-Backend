# Healthcare Backend API

A Django REST Framework backend for user authentication, patient records, doctor records, and patient–doctor assignments. Built to meet the requirements in `Django Assignment_1.pdf`.

## Features

- Django + Django REST Framework + PostgreSQL
- JWT access and refresh tokens using `djangorestframework-simplejwt`
- Email-based registration and login; Django password hashing and password validation
- Patient CRUD, scoped so users can access only patients they created
- Doctor CRUD; all authenticated users can list/view doctors, while only the creator can edit/delete a doctor
- Patient–doctor mappings with duplicate-assignment prevention and ownership checks
- Input validation, structured JSON errors, pagination, doctor filtering/search/order, basic request throttling
- Environment-based settings; no real secrets are committed
- Django admin, automated API tests, Docker Compose for PostgreSQL, Postman collection

## Requirements

- Python 3.11+ (Python 3.12 recommended)
- PostgreSQL 14+ **or Docker Desktop**

## Quick start (Windows PowerShell)

1. Extract the project ZIP and open a terminal in the `healthcare_backend` folder.
2. Create a virtual environment and install dependencies:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. Create the environment file:

   ```powershell
   Copy-Item .env.example .env
   ```

   Edit `.env` and set `DJANGO_SECRET_KEY` to a long random value and set database credentials to match your PostgreSQL instance. Do not commit `.env`.

4. Create the PostgreSQL database and user (run in `psql` as a PostgreSQL administrator; change the password first):

   ```sql
   CREATE USER healthcare_user WITH PASSWORD 'change-this-password';
   CREATE DATABASE healthcare_db OWNER healthcare_user;
   ```

   If your PostgreSQL database/user already exists, use those details in `.env` instead.

5. Create database tables and start the server:

   ```powershell
   python manage.py makemigrations healthcare
   python manage.py migrate
   python manage.py check
   python manage.py runserver
   ```

6. Open `http://127.0.0.1:8000/api/`. The API returns endpoint links. Import `postman/Healthcare_Backend.postman_collection.json` into Postman to test the APIs.

### Quick start using Docker for PostgreSQL

Install and start Docker Desktop, then from this folder run:

```powershell
docker compose up -d db
```

The included `.env.example` values match the Compose database defaults. Then follow steps 2, 3, and 5 above. If port 5432 is already occupied, change the host port in `docker-compose.yml` and set `DB_PORT` to that host port.

### Optional: run the full app in Docker

After creating `.env`, run `docker compose up --build`. The application container runs migrations and starts Django. This development configuration uses Django's development server; for production, use a production WSGI server and hardened deployment settings.

## Authentication flow

1. `POST /api/auth/register/` with `name`, `email`, and `password` (or `first_name` and optional `last_name`).
2. `POST /api/auth/login/` with `email` and `password`.
3. Copy the returned `access` token into the `Authorization` header as `Bearer <access-token>` for protected endpoints.
4. When the access token expires, use `POST /api/auth/token/refresh/` with `{"refresh":"<refresh-token>"}`.

## API endpoints

All endpoints below use JSON. Except registration, login, refresh, and the API root, endpoints require a valid JWT.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/` | API index |
| POST | `/api/auth/register/` | Register a user |
| POST | `/api/auth/login/` | Log in and receive access/refresh tokens |
| POST | `/api/auth/token/refresh/` | Refresh access token |
| POST | `/api/patients/` | Create a patient for the signed-in user |
| GET | `/api/patients/` | List the signed-in user's patients (paginated) |
| GET | `/api/patients/<id>/` | Retrieve one of the signed-in user's patients |
| PUT/PATCH | `/api/patients/<id>/` | Update a patient owned by the signed-in user |
| DELETE | `/api/patients/<id>/` | Delete a patient owned by the signed-in user |
| POST | `/api/doctors/` | Create a doctor |
| GET | `/api/doctors/` | List doctors |
| GET | `/api/doctors/<id>/` | Retrieve a doctor |
| PUT/PATCH | `/api/doctors/<id>/` | Update a doctor (creator only) |
| DELETE | `/api/doctors/<id>/` | Delete a doctor (creator only) |
| POST | `/api/mappings/` | Assign a doctor to a patient |
| GET | `/api/mappings/` | List mappings for the signed-in user's patients |
| GET | `/api/mappings/<patient_id>/` | List doctors mapped to that patient ID |
| DELETE | `/api/mappings/<mapping_id>/` | Remove a mapping by mapping ID |

The assignment uses the same URL pattern for “get mappings for a patient” and “delete a mapping”; the HTTP method distinguishes these actions (GET interprets the ID as a patient ID, DELETE as a mapping ID). A patient must belong to the authenticated user before they can be mapped or queried. Duplicate doctor assignments return HTTP 400.

### Patient request example

```json
{
  "full_name": "Aarav Sharma",
  "age": 35,
  "gender": "male",
  "phone": "+91 9876543210",
  "email": "aarav@example.com",
  "address": "New Delhi",
  "medical_history": "Optional notes"
}
```

Allowed `gender` values: `male`, `female`, `other`, `prefer_not_to_say`.

### Doctor request example

```json
{
  "full_name": "Dr Aditi Rao",
  "specialization": "Cardiology",
  "email": "aditi.rao@example.com",
  "phone": "+91 9876543210",
  "qualifications": "MBBS, MD",
  "experience_years": 8
}
```

### Mapping request example

```json
{
  "patient": 1,
  "doctor": 1
}
```

## Testing

With PostgreSQL running and `.env` configured:

```powershell
python manage.py test healthcare
```

Tests cover registration/login, patient CRUD and user isolation, doctor assignment, duplicate mapping rejection, mapping deletion, and authentication enforcement.

## Admin

Create an admin account with `python manage.py createsuperuser`, then visit `http://127.0.0.1:8000/admin/`.

## Common status codes

- `200 OK`: successful read/update/login
- `201 Created`: resource created
- `204 No Content`: successfully deleted
- `400 Bad Request`: invalid input, duplicate email/assignment, or validation failure
- `401 Unauthorized`: missing/invalid/expired JWT
- `404 Not Found`: resource does not exist or is not accessible to the signed-in user
- `405 Method Not Allowed`: unsupported method

## Security and deployment notes

- Never use the fallback development secret in a deployed environment; set a strong `DJANGO_SECRET_KEY`.
- Set `DJANGO_DEBUG=False`, restrict `DJANGO_ALLOWED_HOSTS`, use strong database credentials, HTTPS, and a production WSGI server before deployment.
- Patient records can contain sensitive data. Use synthetic data for demonstrations and do not commit `.env`, tokens, or real patient data.
- This is an educational backend, not a certified clinical system. Production healthcare systems need further privacy, audit, retention, backup, and regulatory controls.
