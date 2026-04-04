# LearnFlow LMS (Django REST API)

LearnFlow is a backend API for an online learning platform.
It includes user authentication, course management, enrollments, lesson progress tracking, reviews, and async email notifications with Celery.

## Tech Stack

- Django 4.2
- Django REST Framework
- SimpleJWT (JWT auth)
- PostgreSQL
- Celery + Redis
- drf-spectacular (Swagger/ReDoc)

## Project Structure

- `apps/users` → custom user model, auth, profile
- `apps/courses` → categories, courses, sections, lessons
- `apps/enrollments` → enrollments, lesson completion, progress, email tasks
- `apps/reviews` → course reviews and ratings
- `config` → settings, urls, celery app

## Requirements

Install dependencies:

- `pip install -r requirements.txt`

## Environment Variables

Create a `.env` file in project root:

```env
SECRET_KEY=django-insecure-change-me-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=learnflow
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

REDIS_URL=redis://localhost:6379/0

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=LearnFlow <noreply@learnflow.com>
```

## Local Setup

1. Create and activate virtual environment
   - `python -m venv .venv`
   - `source .venv/bin/activate`
2. Install dependencies
   - `pip install -r requirements.txt`
3. Create PostgreSQL database (example: `learnflow`)
4. Run migrations
   - `python manage.py migrate`
5. (Optional) Create superuser
   - `python manage.py createsuperuser`
6. Start API server
   - `python manage.py runserver`

## Celery (Async Tasks)

Start Redis first, then run Celery worker:

- `celery -A config worker --loglevel=info --pool=solo`

> If you see `Cannot connect to redis://localhost:6379/0`, Redis is not running.

## API Documentation

After starting server:

- Swagger UI: `/api/docs/`
- ReDoc: `/api/redoc/`
- OpenAPI schema: `/api/schema/`

## Main API Routes

### Auth
- `POST /api/auth/register/`
- `POST /api/auth/login/`
- `POST /api/auth/token/refresh/`
- `POST /api/auth/logout/`
- `GET/PATCH /api/auth/me/`

### Courses
- `GET /api/categories/`
- `GET/POST /api/courses/`
- `GET/PATCH/DELETE /api/courses/{id}/`
- `POST /api/courses/{id}/publish/`
- `GET/POST /api/courses/{course_id}/sections/`
- `GET/POST /api/courses/{course_id}/sections/{section_id}/lessons/`

### Enrollments & Progress
- `POST /api/courses/{course_id}/enroll/`
- `GET /api/my-courses/`
- `GET /api/courses/{course_id}/progress/`
- `POST /api/lessons/{lesson_id}/complete/`

### Reviews
- `GET/POST /api/courses/{course_id}/reviews/`
- `GET/PATCH/DELETE /api/reviews/{id}/`

## Notes

- `AUTH_USER_MODEL` is custom (`users.User`).
- JWT is enabled globally in DRF settings.
- `.env` and `.venv` are git-ignored.
