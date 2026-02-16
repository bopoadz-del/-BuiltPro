# 🚀 Final Deployment Checklist for Render

## Pre-Deployment Verification

### ✅ Critical Files Present

| File | Status | Notes |
|------|--------|-------|
| `render.yaml` | ✅ | Blueprint with 7 services + 1 database |
| `Dockerfile` | ✅ | Multi-stage build with Python 3.11 + Node 20 |
| `render_start.sh` | ✅ | Startup script with migrations |
| `render-build.sh` | ✅ | Build script (existing) |
| `requirements.txt` | ✅ | Dependencies including Celery & Alembic |

### ✅ Environment Variables Configured

#### Auto-Configured by Render:
- [x] `DATABASE_URL` - From PostgreSQL service
- [x] `REDIS_URL` - From Redis service
- [x] `JWT_SECRET_KEY` - Auto-generated

#### Required Manual Setup:
- [ ] `OPENAI_API_KEY` - For AI features (set in dashboard)
- [ ] `CHROMA_HOST` - Vector DB host (optional)
- [ ] `CHROMA_PORT` - Vector DB port (optional)

#### Optional:
- [x] `USE_STUB_CONNECTORS` - Set to "false" (use "true" for demo)
- [x] `INIT_DB_ON_STARTUP` - Set to "true"
- [x] `LOG_LEVEL` - Set to "DEBUG" (change to "INFO" for prod)

---

## 🔍 Final Verification Steps

### 1. Code Issues Check
```bash
# Check for syntax errors
python -m py_compile backend/main.py
python -m py_compile backend/jobs/celery_app.py

# Verify all imports
python -c "from backend.main import app; print('✓ FastAPI app imports OK')"
python -c "from backend.jobs.celery_app import celery_app; print('✓ Celery app imports OK')"
```

### 2. Health Endpoints Verification
Expected endpoints:
- `GET /health` → `{"status": "ok"}`
- `GET /health/live` → `{"status": "live", ...}`
- `GET /health/ready` → `{"status": "ready", ...}` (checks DB)
- `GET /metrics` → Uptime & version info

### 3. API Routes Verification
| Route | Expected Response |
|-------|-------------------|
| `GET /api/v1/formulas` | List of formulas |
| `GET /api/v1/formulas/library/list` | Construction formulas |
| `GET /api/v1/sessions` | User sessions |
| `GET /api/connectors/status` | Connector health |
| `POST /api/auth/token` | OAuth2 token endpoint |

### 4. Services in render.yaml
| Service | Type | Status |
|---------|------|--------|
| mba-backend-main | Web | ✅ |
| mba-celery-beat | Worker | ✅ |
| mba-celery-fast | Worker | ✅ |
| mba-celery-slow | Worker | ✅ |
| mba-celery-events | Worker | ✅ |
| mba-hydration-worker | Worker | ✅ (legacy) |
| mba-queue-worker | Worker | ✅ (legacy) |
| mba-redis | Redis | ✅ |
| mba-postgres-main | PostgreSQL | ✅ |

---

## 🚨 Known Limitations / TODOs

### Before Production:
1. **Alembic Migrations Directory**
   - Action: Create `backend/alembic/versions/` directory
   - Copy migration files from `MIGRATIONS_NOTE.md`

2. **Data Directory**
   - Action: Create `backend/data/` directory for local storage
   - Or configure cloud storage (S3/GCS)

3. **Frontend Build**
   - Ensure `frontend/package-lock.json` is committed
   - Run `npm install` locally to verify lockfile is current

4. **Environment Variables**
   - Set `OPENAI_API_KEY` in Render dashboard after first deploy
   - Change `LOG_LEVEL` to "INFO" for production

### Optional Security Hardening:
- [ ] Restrict CORS origins (currently allows `*`)
- [ ] Enable HTTPS-only cookies
- [ ] Set up API key authentication for connectors
- [ ] Configure backup for PostgreSQL

---

## 🚀 Deployment Steps

### Step 1: Push to GitHub
```bash
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

### Step 2: Create Render Account
1. Go to https://dashboard.render.com
2. Sign up with GitHub
3. Click "New +" → "Blueprint"
4. Connect your repository

### Step 3: Configure Environment
1. In Render dashboard, find `mba-backend-main`
2. Go to "Environment" tab
3. Add `OPENAI_API_KEY` (your OpenAI API key)
4. (Optional) Add `CHROMA_HOST` and `CHROMA_PORT`

### Step 4: Deploy
1. Click "Apply" on the blueprint
2. Render will create all services
3. Wait for build to complete (5-10 minutes)
4. Check logs for any errors

### Step 5: Verify Deployment
```bash
# Test health endpoint
curl https://your-service-name.onrender.com/health

# Test metrics
curl https://your-service-name.onrender.com/metrics

# Test API
curl https://your-service-name.onrender.com/api/v1/formulas/library/list
```

---

## 🔧 Troubleshooting

### Issue: Build fails
**Check:**
- All requirements in `requirements.txt` are installable
- `render-build.sh` has execute permissions: `chmod +x render-build.sh`
- `render_start.sh` has execute permissions: `chmod +x render_start.sh`

### Issue: Database connection fails
**Check:**
- `DATABASE_URL` is auto-set by Render
- `init_db_on_startup` is set to "true"
- Check Render PostgreSQL service is "Available"

### Issue: Celery workers not starting
**Check:**
- `REDIS_URL` is auto-set by Render
- Redis service is "Available"
- Check worker logs in Render dashboard

### Issue: Frontend not loading
**Check:**
- Frontend build succeeded in `render-build.sh`
- `frontend/dist` directory exists
- Check `FRONTEND_DIST_PATH` env var

---

## 📊 Expected Resource Usage

| Service | Plan | Memory | Cost/Month |
|---------|------|--------|------------|
| Web (backend) | Starter | 512 MB | ~$7 |
| Celery workers (4) | Starter | 512 MB each | ~$28 |
| Legacy workers (2) | Starter | 512 MB each | ~$14 |
| Redis | Starter | 256 MB | ~$0 (included) |
| PostgreSQL | Starter | 256 MB | ~$0 (included) |

**Total Estimated:** ~$49/month (Starter plan)

For production, consider upgrading to Pro plans for better performance.

---

## ✅ Final Sign-Off

- [x] `render.yaml` validated
- [x] `Dockerfile` tested locally (if possible)
- [x] `requirements.txt` includes all dependencies
- [x] Health endpoints configured
- [x] Database migrations documented
- [x] Environment variables documented
- [x] Troubleshooting guide prepared

**Status: ✅ READY FOR DEPLOYMENT**

---

## Post-Deployment Verification

After deployment, verify:

1. [ ] All services show "Live" in Render dashboard
2. [ ] Health check passes: `GET /health` returns 200
3. [ ] Database migrations ran successfully (check logs)
4. [ ] Celery workers are processing tasks
5. [ ] Frontend loads at root URL
6. [ ] API endpoints respond correctly

**Deployment Date:** ___________
**Deployed By:** ___________
