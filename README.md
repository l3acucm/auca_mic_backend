# auca_mic_backend

Django + DRF backend for the AUCA psycholinguistic naming-experiment tool
(see `../BRD.md`). Researchers configure experiments (stimulus images +
answer dictionaries), launch sessions for participants, and participants run
the naming task entirely in the browser (Web Speech API — no server-side
speech recognition, see BRD 6.1). The backend stores experiment configs,
scores each answer against the dictionary, and generates XLSX exports.

Built to the house conventions (presale_backend/cashway_backend): Poetry,
single `settings.py` with `get_env_setting()`, app sub-packages
(`models/ views/ serializers/ services/`), `ModelViewSet` +
`serializers_of_view_actions`, structlog, and **django-moses** for auth.

## Auth — researchers only, admin-created accounts

No self-registration (BRD 1.2/8.7). Create a researcher account with:

```sh
dotenv -f .env run -- poetry run python manage.py shell -c "
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
User = get_user_model()
site = Site.objects.get(id=1)
User.objects.create_superuser(phone_number='+996700000000', password='change-me', site=site)
"
```

**Not** plain `manage.py createsuperuser` — `CustomUser.site` is a required FK
that isn't in moses' `REQUIRED_FIELDS`, so the interactive/`--noinput` command
crashes with `IntegrityError: null value in column "site_id"` (same class of
bug as the registration gotcha in `moses.md`). Passing `site=` explicitly
through the manager sidesteps it.

Login:

1. `POST /moses/token/obtain/` `{phone_number, password, domain}` → `{access, refresh}`.
2. `POST /moses/token/refresh/` `{refresh}` → `{access}`.

`domain` must match the `Site` row in the DB — the
`experiments.0002_set_site_domain` migration sets that Site to the `DOMAIN`
env var on every `migrate`.

Participants never authenticate — they open the unique session URL the
researcher hands them (the Session's UUID, see below).

All API responses are wrapped by moses' renderer as
`{"errors": {...}, "data": {...}}`. Errors use string codes (see
`project/errors.py`).

## Researcher API (`/experiments/`, all `IsAuthenticated`)

| Method | Endpoint | Body | Result |
|---|---|---|---|
| POST | `/experiments/stimulus-sets/` | `{name}` | Creates an empty stimulus set. |
| POST | `/experiments/stimulus-sets/{id}/stimuli/` (multipart) | `image` (jpg/jpeg), `answers` (`;`/`,`-separated) | Uploads one image to storage and adds it to the set's vocab; returns the full set with all stimuli so far. |
| GET | `/experiments/stimulus-sets/` | — | Lists the caller's stimulus sets. |
| GET | `/experiments/stimulus-sets/{id}/` | — | Full detail: every stimulus (filename, answers, image URL) added so far. |
| POST | `/experiments/experiments/` | `name, description, language, num_trials, stimulus_set` | Creates an experiment config. |
| GET/PATCH | `/experiments/experiments/{id}/` | (name, description on PATCH) | Detail / edit — stimuli & vocab are fixed once created. |
| POST | `/experiments/experiments/{id}/archive/` | — | Archives the experiment. |
| POST | `/experiments/experiments/{id}/start-session/` | `{participant_id?}` | Starts a new attempt, returns the `session_url` to hand the participant. |
| GET | `/experiments/results/` | `?experiment=&participant_id=&date_from=&date_to=` | Lists completed attempts. |
| GET | `/experiments/results/{id}/` | — | Full trial-by-trial detail. |
| GET | `/experiments/results/export/?experiment={id}` | — | All participants of one experiment as a single XLSX. |

`ResultListSerializer.download_url` is a presigned S3 URL to the
per-participant XLSX (24h expiry, see `RESULT_DOWNLOAD_URL_EXPIRY_SECONDS`).

## Participant API (`/public/sessions/{session_id}/`, no auth)

| Method | Endpoint | Body | Result |
|---|---|---|---|
| GET | `/public/sessions/{id}/` | — | Session state: language, stimulus count, ordered stimulus image URLs (no vocab — scoring stays server-side). |
| POST | `/public/sessions/{id}/trials/` | `{stimulus_filename, reaction_time_sec, event, timestamp_stimulus, timestamp_speech_start?}` | Records one trial (`event`: `recognized`/`skipped`/`timeout`/`speech_error`) and appends it to the session. |
| POST | `/public/sessions/{id}/complete/` | — | Finalizes the attempt: builds + uploads the XLSX, creates the `Result` row. |

**No transcript.** `onresult` (Chrome's cloud speech-to-text) needs a network
round trip that in practice produced no result at all — every trial hit the
5s failsafe with no error, ever, even during loud sustained speech. Reaction
time is measured stimulus-shown -> `onspeechstart` instead, which is local
voice-activity detection with no network dependency. `event: 'recognized'`
means "a voice was detected", not "said the right word" — `code` is always
`CORRECT` (1) for it now; the vocab/answers a stimulus set stores are kept as
reference metadata for the researcher, not auto-scored against. See BRD
changelog (2026-09-23) for the full reasoning.

## Building a stimulus set

Each stimulus is added individually through the UI/API — pick one image, type
its accepted answers (`;` or `,`-separated, e.g. `жук; букашка`), submit; repeat
for every stimulus. No ZIP/vocab-file upload (dropped 2026-09-22 — see BRD
changelog). The answers are reference metadata for the researcher only — they
are no longer auto-scored against a recognized transcript (dropped
2026-09-23, also in the BRD changelog).

## Local development

```sh
poetry install
cp sample.env .env            # then fill in the values
# Postgres must be running with the DB/role from .env
dotenv -f .env run -- poetry run python manage.py migrate
dotenv -f .env run -- poetry run python manage.py runserver
```

Run tests:

```sh
dotenv -f .env run -- poetry run pytest
```

## Configuration

See [`sample.env`](./sample.env) — every variable is documented there, for
local dev where you set all of them yourself.

**In production**, this app runs on a shared host alongside other apps, split
into `global.env` (shared) + `auca_mic.env` (this app only):

| File | Vars |
|---|---|
| `global.env` (shared, already on the host) | `SECRET_KEY`, `POSTGRES_USER`/`PASSWORD`/`ENDPOINT`/`PORT` (one shared role for every app), `AWS_ACCESS_KEY`/`SECRET_KEY`, `S3_ENDPOINT_URL`, `PRODUCTION` |
| `auca_mic.env` (this app) | `POSTGRES_DATABASE_NAME=auca_mic`, `DOMAIN=micauca-api.vassilyv.me`, `FRONTEND_ORIGINS=https://micauca.vassilyv.me`, `AWS_BUCKET_NAME` (its own bucket) |

Docker Compose loads both (`env_file: [global.env, auca_mic.env]`, see
`compose/auca_mic.yaml` in the shared `presale-agent` compose repo) — Django
just sees the merged result, same `get_env_setting()` either way.

## CI/CD, compose, deploy

- `.github/workflows/build-test-deploy.yaml` — build → self-test (`TESTING=1`
  → pytest against a throwaway Postgres) → push to Docker Hub
  (`l3acucm/auca-mic-backend`) → SSH deploy (`docker compose pull && up -d
  auca_mic_django`, targeted — never `docker compose down` the whole shared
  host).
- `init/auca_mic.sql` — `CREATE DATABASE auca_mic;` on the shared postgres
  role (this host uses one role for every app, not a role per app).
- Compose fragment: `compose/auca_mic.yaml` in the shared `presale-agent`
  compose repo, included (commented until the image + `auca_mic.env` exist).
