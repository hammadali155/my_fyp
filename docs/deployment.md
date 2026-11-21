# Jawhar Deployment Guide

Free-tier deployment of the Jawhar backend (FastAPI) on **Render** with a **Supabase** PostgreSQL database. Total cost: **$0**.

## Architecture

```
┌─────────────┐      HTTPS      ┌──────────────┐      HTTPS      ┌─────────────┐
│  Frontend   │ ───────────────►│  Render      │ ───────────────►│  Supabase   │
│  (KMP app)  │                 │  FastAPI     │                 │  PostgreSQL │
└─────────────┘                 └──────────────┘                 └─────────────┘
                                                    ▲
                                                    │ DATABASE_URL
                                            (set in Render env)
```

- **Render**: hosts the FastAPI backend (free tier, spins down after 15 min inactivity — kept alive via GitHub Actions cron).
- **Supabase**: hosts PostgreSQL (free tier, 500 MB DB, persistent across redeploys).
- **Frontend**: Android APK built locally; optional web target on GitHub Pages/Netlify.

## Prerequisites

1. GitHub account with this repo pushed.
2. Render account (free) — [render.com](https://render.com).
3. Supabase account (free) — [supabase.com](https://supabase.com).

## Step 1: Create the Supabase database

1. Log in to Supabase, create a new project (free tier).
2. Go to **Settings → Database**.
3. Copy the **Connection string** under "URI" (not the pooled one).
4. It looks like:
   ```
   postgresql://postgres.xxx:password@aws-0-xxx.pooler.supabase.com:5432/postgres
   ```
5. Convert it for SQLAlchemy asyncpg driver — prefix with `postgresql+asyncpg://` and append `?sslmode=require`:
   ```
   postgresql+asyncpg://postgres.xxx:password@aws-0-xxx.pooler.supabase.com:5432/postgres?sslmode=require
   ```
6. Save this — you'll paste it into Render as `DATABASE_URL`.

## Step 2: Create the Render web service

1. Log in to Render, click **New → Web Service**.
2. Connect your GitHub repo `magic-meer/fyp`.
3. Render should detect `render.yaml` at the repo root. If it asks you to configure manually instead, use these settings:

| Setting | Value |
|---------|-------|
| **Runtime** | Python |
| **Build command** | `pip install uv && uv sync --frozen --no-cache && uv run alembic upgrade head` |
| **Start command** | `uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| **Root directory** | `backend` |
| **Plan** | Free |
| **Region** | Oregon (or closest to you) |
| **Health check path** | `/health/live` |
| **Auto-deploy** | Yes (on push to your branch) |

4. Add **Environment Variables** in the Render dashboard:

| Key | Value | Required? |
|-----|-------|-----------|
| `DATABASE_URL` | Your Supabase connection string from Step 1 | Yes |
| `JWT_SECRET` | Any strong random string (Render can generate one) | Yes |
| `CORS_ORIGINS` | `["*"]` (or your frontend domain) | No |
| `DEBUG` | `false` | No |
| `LOG_LEVEL` | `INFO` | No |
| `GEMINI_API_KEY` | Only if using AI tutor; leave empty to disable | No |
| `GEMINI_MODEL` | `gemini-2.0-flash` | No |

5. Click **Create Web Service**. Render will:
   - Clone the repo
   - Run the build command (installs deps with `uv`, runs Alembic migrations against Supabase)
   - Start the uvicorn server on `$PORT`

## Step 3: Verify the backend is live

Once the build succeeds, open:
```
https://jawhar-backend.onrender.com/health/live
```
You should see `{"status":"alive"}`.

Also check:
```
https://jawhar-backend.onrender.com/health/ready   (database ping)
https://jawhar-backend.onrender.com/docs            (interactive API docs)
```

## Step 4: Keep the backend awake (Render free tier)

Render free web services spin down after 15 minutes of inactivity. The repo includes a GitHub Actions cron that pings `/health/live` every 14 minutes.

1. Go to your GitHub repo **Settings → Secrets and variables → Actions**.
2. Add a new repository secret:
   - Name: `RENDER_BACKEND_URL`
   - Value: `https://jawhar-backend.onrender.com` (your actual Render URL)
3. The workflow `.github/workflows/keep-alive.yml` will run on schedule `*/14 * * * *` and can also be triggered manually via the Actions tab.

## Step 5: Connect the frontend

The desktop JVM build points to `http://localhost:8000`. Update it to your Render URL:

**File:** `shared/src@jvm/data/api/ApiClient.jvm.kt`

```kotlin
actual fun defaultApiBaseUrl(): String = "https://jawhar-backend.onrender.com"
```

Rebuild the desktop app:
```bash
./kotlin run -m desktopApp
```

For Android, build the APK locally and install on your device — it uses the same `defaultApiBaseUrl()` from its platform source set.

## Step 6: Local development (optional)

If you want to run the backend locally before deploying:

```bash
cd backend
cp .env.example .env
# Edit .env if you want to use Supabase instead of SQLite
uv sync
uv run alembic upgrade head
uv run fastapi dev app/main.py
```

Then verify:
```bash
curl http://localhost:8000/health/live
```

## Repository structure for deployment

```
.
├── render.yaml                  # Render service definition (rootDir: backend)
├── .github/
│   └── workflows/
│       └── keep-alive.yml       # Pings /health/live every 14 min
├── backend/
│   ├── Dockerfile               # Multi-stage Docker build (alternative platforms)
│   ├── .env.example             # Template for local .env (gitignored)
│   ├── .env                     # Local secrets — NOT committed
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── app/                     # FastAPI application
│   └── alembic/                 # DB migrations
├── shared/                      # Kotlin Multiplatform module
│   └── src@jvm/
│       └── data/api/
│           └── ApiClient.jvm.kt # defaultApiBaseUrl() → your Render URL
└── AGENTS.md                    # Project context (deployment section updated)
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Build fails: `No pyproject.toml found` | Ensure `render.yaml` has `rootDir: backend` |
| App crashes on startup | Check `DATABASE_URL` is set in Render env vars |
| `/health/ready` returns 503 | Supabase connection string may be wrong or SSL missing |
| Backend spins down after inactivity | Expected on Render free — the keep-alive cron handles it |
| Frontend can't connect | Update `defaultApiBaseUrl()` in `ApiClient.jvm.kt` to your Render URL |
| `JWT_SECRET` missing | Render can auto-generate one; set it manually in env vars |

## Why not sub-repos?

Keeping backend + frontend in one monorepo is the right call for a 2-person FYP:

- **Shared `shared/` module** is used by both frontend and backend tests — splitting repos means duplicating or version-pinning it.
- **Atomic changes**: one PR can touch a new backend endpoint and its frontend wiring together.
- **One CI config** instead of N.

The only downside is Render rebuilding the backend on frontend-only pushes. That's a ~1–2 minute free rebuild — harmless. If it bothers you, set `autoDeploy: false` in `render.yaml` and trigger backend deploys manually.

## Future platforms

The `backend/Dockerfile` is kept so you can move to Railway, Koyeb, Oracle Cloud, or Google Cloud later without rewriting build instructions. Render free tier uses native Python (not Docker), so `render.yaml` is the active config for now.
