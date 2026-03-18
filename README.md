# 💘 Dating App

Een dating app API gebouwd met **FastAPI**, **PostgreSQL** en **Docker**.

## Features

- **Registratie & Login** (JWT authenticatie)
- **Profielen** aanmaken, bekijken en bewerken
- **Discover** – profielen zien die je nog niet hebt geswiped
- **Swipen** – like / dislike op profielen
- **Matches** – automatisch matchen bij wederzijdse like

## Quick Start

```bash
# Start alles met Docker Compose
docker compose up -d --build

# API is beschikbaar op:
# http://localhost:8000

# Swagger docs:
# http://localhost:8000/docs
```

## API Endpoints

| Methode | Endpoint                | Beschrijving                     |
|---------|------------------------|----------------------------------|
| POST    | `/api/auth/register`   | Account aanmaken                 |
| POST    | `/api/auth/login`      | Inloggen (geeft JWT token)       |
| POST    | `/api/profiles/`       | Profiel aanmaken                 |
| GET     | `/api/profiles/me`     | Eigen profiel bekijken           |
| PATCH   | `/api/profiles/me`     | Profiel bewerken                 |
| GET     | `/api/profiles/`       | Discover – nieuwe profielen      |
| GET     | `/api/profiles/{id}`   | Profiel bekijken op ID           |
| POST    | `/api/matches/swipe`   | Swipen (like/dislike)            |
| GET     | `/api/matches/`        | Al je matches bekijken           |
| GET     | `/health`              | Health check                     |

## Voorbeeld: Registreren + Profiel aanmaken

```bash
# 1. Registreren
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "wachtwoord123"}'

# Antwoord: {"access_token": "eyJ...", "token_type": "bearer"}

# 2. Profiel aanmaken (gebruik de token uit stap 1)
curl -X POST http://localhost:8000/api/profiles/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJ..." \
  -d '{
    "display_name": "Ahmed",
    "age": 25,
    "gender": "male",
    "bio": "Ik hou van reizen en koken",
    "city": "Amsterdam"
  }'
```

## Productie tips

1. Verander `SECRET_KEY` in `.env` (gebruik `openssl rand -hex 32`)
2. Verander database wachtwoord
3. Beperk CORS origins in `app/main.py`
4. Gebruik Alembic voor database migraties
5. Voeg rate limiting toe
