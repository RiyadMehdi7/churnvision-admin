"""
Installation Package Generator Service

Generates docker-compose.yml, .env, and README files for customer installations.
"""

import io
import zipfile
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.models.tenant import Tenant
from app.models.license import License
from app.core.config import settings


def get_active_license(db: Session, tenant_id: str) -> Optional[License]:
    """Get the most recent active license for a tenant"""
    return (
        db.query(License)
        .filter(
            License.tenant_id == tenant_id,
            License.revoked == False,
            License.expires_at > datetime.utcnow(),
        )
        .order_by(License.expires_at.desc())
        .first()
    )


def generate_docker_compose(
    tenant: Tenant,
    docker_image: str = "ghcr.io/riyadmehdi7/churnvision_web_1_0:latest",
    admin_api_url: str = None,
) -> str:
    """Generate docker-compose.yml content"""

    return f"""version: '3.8'

services:
  churnvision:
    image: {docker_image}
    container_name: churnvision-{tenant.slug}
    restart: unless-stopped
    ports:
      - "3000:3000"
    env_file:
      - .env
    environment:
      # These override .env values if needed
      - DATABASE_URL=${{DATABASE_URL}}
      - REDIS_URL=${{REDIS_URL:-redis://redis:6379/0}}
      - SECRET_KEY=${{SECRET_KEY}}
      - LICENSE_KEY=${{LICENSE_KEY}}
      - TENANT_SLUG=${{TENANT_SLUG}}
      - ADMIN_API_URL=${{ADMIN_API_URL}}
      - ADMIN_API_KEY=${{ADMIN_API_KEY}}
      - LICENSE_VALIDATION_MODE=${{LICENSE_VALIDATION_MODE:-hybrid}}
      - ENVIRONMENT=${{ENVIRONMENT:-production}}
      - DEBUG=${{DEBUG:-false}}
      - ALLOWED_ORIGINS=${{ALLOWED_ORIGINS:-http://localhost:3000}}
      - ENCRYPTION_KEY=${{ENCRYPTION_KEY}}
    volumes:
      - churnvision_data:/app/churnvision_data
      - churnvision_models:/app/models
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - churnvision-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  db:
    image: postgres:15-alpine
    container_name: churnvision-{tenant.slug}-db
    restart: unless-stopped
    environment:
      - POSTGRES_USER=${{POSTGRES_USER:-churnvision}}
      - POSTGRES_PASSWORD=${{POSTGRES_PASSWORD}}
      - POSTGRES_DB=${{POSTGRES_DB:-churnvision}}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - churnvision-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${{POSTGRES_USER:-churnvision}}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: churnvision-{tenant.slug}-redis
    restart: unless-stopped
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lfu
    volumes:
      - redis_data:/data
    networks:
      - churnvision-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

volumes:
  postgres_data:
  redis_data:
  churnvision_data:
  churnvision_models:

networks:
  churnvision-network:
    driver: bridge
"""


def generate_env_file(
    tenant: Tenant, license_key: str, admin_api_url: str, admin_api_key: str
) -> str:
    """Generate .env file content"""
    import secrets

    # Generate secure random keys
    secret_key = secrets.token_urlsafe(32)
    encryption_key_hint = '# Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'

    return f"""# ChurnVision Configuration for {tenant.name}
# Generated: {datetime.utcnow().isoformat()}
# DO NOT SHARE THIS FILE - Contains sensitive credentials

# ===== Environment =====
ENVIRONMENT=production
DEBUG=false

# ===== License Configuration =====
LICENSE_KEY={license_key}
TENANT_SLUG={tenant.slug}

# ===== Admin Panel Connection =====
ADMIN_API_URL={admin_api_url}
ADMIN_API_KEY={admin_api_key}
LICENSE_VALIDATION_MODE=hybrid

# ===== Security Configuration =====
# IMPORTANT: Keep these secret keys secure!
SECRET_KEY={secret_key}
{encryption_key_hint}
ENCRYPTION_KEY=GENERATE_AND_SET_THIS

# ===== Database Configuration =====
# IMPORTANT: Change the password below!
DATABASE_URL=postgresql+asyncpg://churnvision:CHANGE_THIS_PASSWORD@db:5432/churnvision
POSTGRES_USER=churnvision
POSTGRES_PASSWORD=CHANGE_THIS_PASSWORD
POSTGRES_DB=churnvision

# ===== Redis Configuration =====
REDIS_URL=redis://redis:6379

# ===== CORS Configuration =====
# Add your frontend URL(s) here, comma-separated
ALLOWED_ORIGINS=http://localhost:3000

# ===== Application Settings =====
# Uncomment and modify as needed
# LOG_LEVEL=INFO
"""


def generate_readme(tenant: Tenant, docker_image: str) -> str:
    """Generate README.md with installation instructions"""

    return f"""# ChurnVision Installation Guide

## Customer: {tenant.name}
## Tenant ID: {tenant.slug}
## Generated: {datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}

---

## Prerequisites

1. **Docker** - Install from https://docs.docker.com/get-docker/
2. **Docker Compose** - Usually included with Docker Desktop
3. **Minimum System Requirements:**
   - 4 GB RAM
   - 2 CPU cores
   - 20 GB disk space

### Quick Docker Installation (Linux)
```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# Log out and back in for group changes to take effect
```

---

## Installation Steps

### 1. Extract this package
```bash
unzip churnvision-{tenant.slug}.zip
cd churnvision-{tenant.slug}
```

### 2. Configure the environment (IMPORTANT!)
Edit the `.env` file and make these changes:

**Required Changes:**
- `POSTGRES_PASSWORD` - Set a secure database password (min 16 characters)
- `DATABASE_URL` - Update with the same password you set above
- `ENCRYPTION_KEY` - Generate and set (see command below)

**Generate Encryption Key:**
```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**Optional but Recommended:**
- `ALLOWED_ORIGINS` - Set to your domain(s) if not using localhost

```bash
nano .env
# or
vim .env
```

### 3. Start ChurnVision
```bash
docker-compose up -d
```

### 4. Wait for services to be healthy
```bash
# Check status (all should show "healthy")
docker-compose ps

# Watch logs during startup
docker-compose logs -f
```

### 5. Access the application
Open your browser and go to: **http://localhost:3000**

Default admin credentials will be created on first run.

---

## Useful Commands

```bash
# View logs
docker-compose logs -f churnvision

# View all service logs
docker-compose logs -f

# Stop the application
docker-compose down

# Restart the application
docker-compose restart

# Check service health
docker-compose ps

# Update to latest version
docker-compose pull
docker-compose up -d
```

---

## Updating ChurnVision

When a new version is available:

```bash
# Pull the latest image
docker-compose pull

# Restart with new version (preserves data)
docker-compose up -d

# Verify update
docker-compose ps
```

---

## Backup & Restore

### Backup Database
```bash
docker-compose exec db pg_dump -U churnvision churnvision > backup.sql
```

### Restore Database
```bash
docker-compose exec -T db psql -U churnvision churnvision < backup.sql
```

---

## Troubleshooting

### Application won't start
```bash
# Check logs for errors
docker-compose logs churnvision

# Verify all containers are running
docker-compose ps

# Check if services are healthy
docker-compose ps --format "table {{{{.Name}}}}\\t{{{{.Status}}}}"
```

### Database connection issues
```bash
# Check if database is running
docker-compose logs db

# Restart database
docker-compose restart db

# Verify database is healthy
docker-compose exec db pg_isready -U churnvision
```

### License validation errors
- Ensure your server has internet access to reach the Admin Panel
- Check that `ADMIN_API_URL` and `ADMIN_API_KEY` in `.env` are correct
- The application works offline for up to 30 days (grace period)
- Check logs: `docker-compose logs churnvision | grep -i license`

### Redis connection issues
```bash
docker-compose logs redis
docker-compose restart redis
```

---

## Security Notes

1. **Change all default passwords** before deploying to production
2. **Keep your `.env` file secure** - it contains sensitive credentials
3. **Use HTTPS** in production (configure a reverse proxy like nginx or traefik)
4. **Regular backups** - schedule automated database backups

---

## Support

For assistance, contact your ChurnVision administrator.

---

## Technical Details

- **Docker Image:** {docker_image}
- **Tier:** {tenant.tier.value}
- **Max Employees:** {tenant.max_employees or "Unlimited"}
- **Max Users:** {tenant.max_users}
- **License Mode:** Hybrid (online validation with offline fallback)
- **Offline Grace Period:** 30 days
"""


def generate_installation_package(
    db: Session,
    tenant: Tenant,
    docker_image: str = "ghcr.io/riyadmehdi7/churnvision_web_1_0:latest",
    admin_api_url: str = None,
    admin_api_key: str = None,
) -> bytes:
    """
    Generate a complete installation package as a ZIP file.

    Returns: bytes of the ZIP file
    """
    # Get active license
    license = get_active_license(db, str(tenant.id))
    if not license:
        raise ValueError(f"No active license found for tenant {tenant.slug}")

    # Use provided or default values
    if not admin_api_url:
        admin_api_url = "https://churnvision-admin-api.onrender.com/api/v1"
    if not admin_api_key:
        admin_api_key = settings.API_KEY

    # Generate file contents
    docker_compose = generate_docker_compose(tenant, docker_image, admin_api_url)
    env_file = generate_env_file(
        tenant, license.key_string, admin_api_url, admin_api_key
    )
    readme = generate_readme(tenant, docker_image)

    # Create ZIP file in memory
    zip_buffer = io.BytesIO()

    folder_name = f"churnvision-{tenant.slug}"

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr(f"{folder_name}/docker-compose.yml", docker_compose)
        zip_file.writestr(f"{folder_name}/.env", env_file)
        zip_file.writestr(f"{folder_name}/README.md", readme)

    zip_buffer.seek(0)
    return zip_buffer.getvalue()
