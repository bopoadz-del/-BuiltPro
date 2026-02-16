# `-builtPro` Repository Audit Report

## Date: 2026-02-16

---

## 1. FastAPI Wiring Status ✅

### Main Entry Points:
| File | Status | Notes |
|------|--------|-------|
| `main.py` (root) | ✅ Wired | Full implementation with dynamic router loading |
| `backend/main.py` | ✅ Wired | Static imports for v1 API routes |

### Router Loading:
- Root `main.py`: Dynamic loading with graceful degradation (29 routers)
- `backend/main.py`: Static imports for v1 endpoints

---

## 2. Render.yaml Blueprint Compliance ✅

### Services Configured:
- **Web Service**: `mba-backend-main` (Python 3.11.9)
- **Worker Services**:
  - `mba-hydration-worker`
  - `mba-queue-worker`
  - `mba-event-projector`
- **Redis**: `mba-redis`
- **Database**: `mba-postgres-main`

### Environment Variables: ✅ All required vars configured
- DATABASE_URL, REDIS_URL, OPENAI_API_KEY
- JWT_SECRET_KEY (auto-generated)
- INIT_DB_ON_STARTUP: true
- DEMO_SEED_SOURCES: true

---

## 3. CI/CD Workflow Status ⚠️

### Missing File:
- ❌ `.github/workflows/regen-frontend-lockfile.yml` - NOT FOUND

### Existing Workflow:
- ✅ `.github/workflows/enterprise-ci-cd.yml` - Present with lint, test, security-audit, build, deploy jobs

---

## 4. Docker & Build Configuration ✅

### Files:
- ✅ `Dockerfile` - Multi-stage build (Python + Node)
- ✅ `render-build.sh` - Comprehensive build script with venv support
- ✅ `docker-compose.yml` - Stack configuration
- ✅ `docker-compose.override.yml` - Local dev overrides

---

## 5. Formula Runtime Status ✅

### Implementation:
- ✅ `backend/api/runtime.py` - FULLY IMPLEMENTED (277 lines)
- Endpoints: `/runtime/execute`, `/runtime/generate`, `/runtime/history`, `/runtime/functions`, `/runtime/validate`
- Sandbox execution with safety validation
- Execution history tracking

### Schema:
- ✅ `backend/runtime/schemas.py` - All schemas defined
- ✅ `backend/runtime/sandbox.py` - Sandbox executor
- ✅ `backend/runtime/function_registry.py` - Approved functions

---

## 6. Session/Conversation Endpoints ⚠️

### Status:
- ⚠️ Chat endpoints are STUBS in `backend/api/v1/chat.py`
- ⚠️ `backend/api/chat_routes.py` - Only placeholder, returns 501
- ✅ Full chat implementation exists in `backend/api/chat.py` (main app)

---

## 7. Celery/Redis Configuration ⚠️

### Findings:
- ❌ **NO CELERY CONFIGURATION FOUND**
- ✅ Redis Streams queue worker: `backend/jobs/queue_worker.py` (284 lines)
- ✅ Redis Queue implementation: `backend/redisx/queue.py`
- ✅ Queue worker uses custom Redis Streams implementation (not Celery)

### Migration Note:
The app uses a **custom Redis Streams** implementation instead of Celery. This is a valid architectural choice.

---

## 8. API Security Hardening ⚠️

### Current State:
| Component | Status | Issue |
|-----------|--------|-------|
| Rate Limiting | ✅ | `slowapi` integrated in `backend/main.py` |
| CORS | ⚠️ | Wildcard allowed, credentials disabled in prod |
| JWT Auth | ✅ | Implemented with HS256 |
| Password Hashing | ✅ | bcrypt via passlib |
| `backend/core/security.py` | ❌ | Returns HARDCODED dummy user |
| `backend/api/deps.py` | ✅ | Proper auth with token verification |

### Critical Issue:
```python
# backend/core/security.py - LINE 18-32
def get_current_user() -> User:
    return User(id=1, username="demo")  # HARDCODED! ⚠️
```

---

## 9. Health/Readiness Endpoints ✅

### Implementation:
- ✅ `/health` - Basic health check
- ✅ `/healthz` - Alias
- ✅ `/livez` - Liveness probe
- ✅ `/readyz` - Readiness probe with DB check

---

## 10. Dependency Pins ✅

### Files:
- ✅ `requirements.txt` - Root requirements (50 deps)
- ✅ `backend/requirements.txt` - Backend-specific (35 deps)
- ✅ `requirements-ml-optional.txt` - ML optional
- ✅ `requirements-dev.txt` - Dev dependencies

### All versions pinned with `==` ✅

---

## 11. Placeholder Audit ⚠️ CRITICAL

### STUB Implementations Found:

| File | Lines | Status | Issue |
|------|-------|--------|-------|
| `backend/api/v1/chat.py` | 21 | ❌ STUB | Only returns status message |
| `backend/api/v1/formulas.py` | 21 | ❌ STUB | Only returns status message |
| `backend/api/v1/auditor.py` | 21 | ❌ STUB | Only returns status message |
| `backend/api/self_coding_routes.py` | 26 | ❌ STUB | Returns placeholder code |
| `backend/api/auth_routes.py` | 90 | ⚠️ PARTIAL | In-memory user store, fake tokens |
| `backend/core/security.py` | 32 | ❌ STUB | Hardcoded user |

### FULL Implementations:

| File | Lines | Status |
|------|-------|--------|
| `backend/api/runtime.py` | 277 | ✅ FULL |
| `backend/api/reasoning.py` | 356 | ✅ FULL |
| `backend/api/v1/schedule_analysis.py` | 125 | ✅ FULL |
| `backend/api/v1/pdf_analysis.py` | 69 | ✅ FULL |
| `backend/api/connectors.py` | 112 | ✅ FULL |

---

## 12. Connector API Wiring ✅

### Services Integrated:
- ✅ Google Drive
- ✅ Oracle Aconex
- ✅ Primavera P6
- ✅ BIM/IFC
- ✅ Vision/Photo
- ✅ OneDrive
- ✅ Power BI
- ✅ Microsoft Teams

---

## 13. Database Models ✅

### Files:
- ✅ `backend/models/auth.py` - User, roles
- ✅ `backend/backend/models.py` - Core models
- ✅ `backend/db.py` - Database connection
- ✅ Alembic migrations configured

---

## CRITICAL ISSUES TO FIX:

### Priority 1 (Security):
1. ❌ `backend/core/security.py` - Hardcoded user (MAJOR SECURITY RISK)
2. ❌ `backend/api/auth_routes.py` - Fake tokens, in-memory store

### Priority 2 (Functionality):
3. ⚠️ `backend/api/v1/chat.py` - Stub implementation
4. ⚠️ `backend/api/v1/formulas.py` - Stub implementation
5. ⚠️ `backend/api/v1/auditor.py` - Stub implementation

### Priority 3 (CI/CD):
6. ❌ Missing `regen-frontend-lockfile.yml` workflow

---

## Summary

| Category | Score | Notes |
|----------|-------|-------|
| Infrastructure | 9/10 | Render, Docker, Redis all good |
| API Routes | 7/10 | Core routes done, v1 stubs need work |
| Security | 5/10 | Critical auth issues |
| Documentation | 8/10 | Good READMEs and docs |
| Testing | 7/10 | Tests exist but may not cover stubs |

**Overall: 7.2/10** - Good foundation but security issues must be fixed.
