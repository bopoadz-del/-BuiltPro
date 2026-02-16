# Data Directory Setup

## For Docker/Render Deployment

The `backend/data/` directory should be created for local data storage.

### To create manually:
```bash
mkdir -p backend/data
```

### Docker Volume Mount
In `render.yaml` or `docker-compose.yml`, mount this directory as a persistent volume:
```yaml
volumes:
  - data:/app/backend/data
```

### Contents
This directory stores:
- Local file uploads (when not using cloud storage)
- Temporary processing files
- Local cache data
- Session backups

**Note**: Do not commit sensitive data in this directory to git.
