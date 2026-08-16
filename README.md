# Videoflix Backend

This project is the Django REST Framework backend for the **Videoflix Frontend**, a Netflix-style video streaming platform.

> **Developer Akademie learning project** — The backend was independently developed to fully connect to the given frontend and implement authentication, video upload/management, and adaptive HLS video streaming.

---

## About the Project

Videoflix lets registered and activated users browse a video catalog and stream videos via HLS in multiple resolutions (480p/720p/1080p). Videos are uploaded via the Django admin panel; a background worker converts each upload into HLS renditions and — if no thumbnail was provided — automatically generates one from a frame of the video. Authentication uses JWT stored in HttpOnly cookies, with email-based account activation and password reset.

---

## Tech Stack

| Technology | Version |
|---|---|
| Python | 3.12+ |
| Django | 6.0.7 |
| Django REST Framework | 3.17.1 |
| Authentication | JWT via HttpOnly cookies (`djangorestframework-simplejwt`) |
| Database | PostgreSQL |
| Background Jobs | Redis Queue (`django-rq`) |
| Video Processing | `ffmpeg` (HLS conversion, thumbnail extraction) |
| Container | Docker / Docker Compose |

---

## Installation & Setup

The project is fully containerized. You only need Docker Desktop installed — no local Python, PostgreSQL, Redis, or ffmpeg setup required.

```bash
# 1. Clone the repository
git clone https://github.com/lucasxgraf/videoflix_backend.git
cd videoflix_backend
```

```bash
# 2. Create your local .env file from the provided template
cp .env.example .env
```

Open `.env` and fill in your own values. At minimum, set real values for `DB_NAME`, `DB_USER`, `DB_PASSWORD`, and `SECRET_KEY`. For the activation/password-reset emails to actually be delivered, set `EMAIL_HOST`, `EMAIL_HOST_USER`, and `EMAIL_HOST_PASSWORD` to a real SMTP account (e.g. a Gmail account with an [app password](https://myaccount.google.com/apppasswords)).

`FRONTEND_URL` and `BACKEND_URL` default to `http://localhost:5500` and `http://localhost:8000`. Leave them as-is if you run the frontend via a local Live Server on port 5500 — the activation link, password-reset link, and email logo are all built from these two values.

```bash
# 3. Build and start all containers (web, db, redis)
docker compose up --build
```

This single command:
- builds the Django image and installs all dependencies (including `ffmpeg`, baked into the image)
- waits for PostgreSQL to become ready
- runs `collectstatic`, `makemigrations`, and `migrate`
- creates a Django superuser from `DJANGO_SUPERUSER_EMAIL` / `DJANGO_SUPERUSER_PASSWORD` (only if it doesn't already exist)
- starts a background RQ worker (handles HLS conversion, thumbnail generation, and email sending)
- starts the Gunicorn server

The API is then available at `http://127.0.0.1:8000/api/`.
The Django admin is available at `http://127.0.0.1:8000/admin/` (login with the `DJANGO_SUPERUSER_EMAIL` / `DJANGO_SUPERUSER_PASSWORD` from your `.env`).

To stop the containers:

```bash
docker compose down
```

To restart after changing `.py` files (Gunicorn auto-reloads on code changes, but the background RQ worker does **not** — it needs a manual restart to pick up new task code):

```bash
docker compose restart web
```

### Uploading a video

1. Go to `http://127.0.0.1:8000/admin/` and log in.
2. Under **Video app → Videos**, click **Add video**.
3. Fill in title, description, category, and upload the video file. Thumbnail is optional — if left empty, one is automatically generated from the video.
4. Save. The background worker converts the video to HLS (480p/720p/1080p) and generates the thumbnail if needed; `processing_status` changes from `pending` → `processing` → `done`. Only videos with status `done` are returned by the API and playable.

### Connecting the frontend

The frontend expects the backend at `http://127.0.0.1:8000`. If you run the frontend via VS Code's Live Server (default port `5500`), no further configuration is needed — CORS is already configured for `http://localhost:5500` and `http://127.0.0.1:5500` by default (see `CORS_ALLOWED_ORIGINS` in `.env.example`). If your frontend runs on a different origin, add it to `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS` in `.env`.

---

## API Endpoints

### Auth (`/api/`)

| Method | Endpoint | Description |
|---|---|---|
| POST | `register/` | Register a new (inactive) user, sends an activation email |
| GET | `activate/<uidb64>/<token>/` | Activate the account (called by the frontend's activation page) |
| POST | `login/` | Log in, sets `access_token` / `refresh_token` HttpOnly cookies |
| POST | `logout/` | Blacklist the refresh token and clear auth cookies |
| POST | `token/refresh/` | Issue a new access token cookie from the refresh token cookie |
| POST | `password_reset/` | Request a password reset email for the given address |
| POST | `password_confirm/<uidb64>/<token>/` | Set a new password via the link from the reset email |

### Video (`/api/`) — all require authentication

| Method | Endpoint | Description |
|---|---|---|
| GET | `video/` | List all videos (newest first) |
| GET | `video/<movie_id>/<resolution>/index.m3u8` | HLS manifest for a video/resolution (`480p`, `720p`, `1080p`) |
| GET | `video/<movie_id>/<resolution>/<segment>` | Individual `.ts` HLS segment |

---

## Project Structure

```
videoflix_backend/
├── core/                       # Project settings, root URLs
├── auth_app/                   # Registration, activation, JWT cookie auth, password reset
│   ├── api/
│   │   ├── serializers.py
│   │   ├── utils.py            # Cookie & token helpers
│   │   └── views.py
│   ├── templates/email/        # Activation & password-reset email templates
│   ├── tasks.py                # RQ background jobs: sending emails
│   └── tests/
├── video_app/                  # Video model, HLS streaming, thumbnail generation
│   ├── api/
│   │   ├── serializers.py
│   │   └── views.py            # Video list, HLS manifest/segment delivery
│   ├── ffmpeg.py                # ffmpeg wrappers: HLS conversion, thumbnail extraction
│   ├── tasks.py                 # RQ background job: HLS conversion + thumbnail generation
│   ├── signals.py               # Triggers conversion on upload, cleans up files on delete
│   └── tests/
├── backend.Dockerfile
├── backend.entrypoint.sh
├── docker-compose.yml
├── manage.py
├── requirements.txt
├── .env.example
└── .env                         # not committed, created from .env.example
```

---

## Running Tests

```bash
docker compose exec web python manage.py test
```

---

## Notes

- `DEBUG=True` and `FRONTEND_URL`/`BACKEND_URL` pointing at `localhost` are intended for local grading/testing, where the reviewer runs the whole stack and opens the frontend on the same machine. For a real deployment, set `DEBUG=False`, `ALLOWED_HOSTS`/`CORS_ALLOWED_ORIGINS`/`CSRF_TRUSTED_ORIGINS` to the real domains, and serve `/media/` via a webserver in front of Django (Django only serves it itself while `DEBUG=True`).
- Keep `DEBUG=True` for local HTTP testing: the `access_token`/`refresh_token` cookies are only marked `Secure` when `DEBUG=False`, since browsers silently refuse to store `Secure` cookies over plain HTTP (no login session would ever persist locally otherwise). This is only safe because production deployments (`DEBUG=False`) are expected to run behind HTTPS.
- The email logo is embedded directly into outgoing emails (not linked as a remote image), so it displays correctly even in clients like Gmail that fetch remote images through their own proxy and can't reach a `localhost` backend.
