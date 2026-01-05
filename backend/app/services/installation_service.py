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
    docker_image: str = "ghcr.io/riyadmehdi7/churnvision:latest",
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
    environment:
      - DATABASE_URL=${{DATABASE_URL}}
      - REDIS_URL=${{REDIS_URL:-redis://redis:6379}}
      - LICENSE_KEY=${{LICENSE_KEY}}
      - TENANT_SLUG=${{TENANT_SLUG}}
      - ADMIN_API_URL=${{ADMIN_API_URL}}
      - ADMIN_API_KEY=${{ADMIN_API_KEY}}
      - LICENSE_VALIDATION_MODE=${{LICENSE_VALIDATION_MODE:-hybrid}}
    depends_on:
      - db
      - redis
    networks:
      - churnvision-network

  db:
    image: postgres:15
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

  redis:
    image: redis:7-alpine
    container_name: churnvision-{tenant.slug}-redis
    restart: unless-stopped
    networks:
      - churnvision-network

volumes:
  postgres_data:

networks:
  churnvision-network:
    driver: bridge
"""


def generate_env_file(
    tenant: Tenant, license_key: str, admin_api_url: str, admin_api_key: str
) -> str:
    """Generate .env file content"""

    return f"""# ChurnVision Configuration for {tenant.name}
# Generated: {datetime.utcnow().isoformat()}
# DO NOT SHARE THIS FILE - Contains sensitive credentials

# ===== License Configuration =====
LICENSE_KEY={license_key}
TENANT_SLUG={tenant.slug}

# ===== Admin Panel Connection =====
ADMIN_API_URL={admin_api_url}
ADMIN_API_KEY={admin_api_key}
LICENSE_VALIDATION_MODE=hybrid

# ===== Database Configuration =====
DATABASE_URL=postgresql://churnvision:CHANGE_THIS_PASSWORD@db:5432/churnvision
POSTGRES_USER=churnvision
POSTGRES_PASSWORD=CHANGE_THIS_PASSWORD
POSTGRES_DB=churnvision

# ===== Redis Configuration =====
REDIS_URL=redis://redis:6379

# ===== Application Settings =====
# Uncomment and modify as needed
# APP_PORT=3000
# LOG_LEVEL=INFO
# DEBUG=false
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

### 2. Configure the environment
Edit the `.env` file and change:
- `POSTGRES_PASSWORD` - Set a secure database password
- Update `DATABASE_URL` with the same password

```bash
nano .env
# or
vim .env
```

### 3. Start ChurnVision
```bash
docker-compose up -d
```

### 4. Access the application
Open your browser and go to: **http://localhost:3000**

---

## Useful Commands

```bash
# View logs
docker-compose logs -f churnvision

# Stop the application
docker-compose down

# Restart the application
docker-compose restart

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

# Restart with new version
docker-compose up -d
```

---

## Troubleshooting

### Application won't start
```bash
# Check logs for errors
docker-compose logs churnvision

# Verify all containers are running
docker-compose ps
```

### Database connection issues
```bash
# Check if database is running
docker-compose logs db

# Restart database
docker-compose restart db
```

### License validation errors
- Ensure your server has internet access to reach the Admin Panel
- Check that `ADMIN_API_URL` and `ADMIN_API_KEY` in `.env` are correct
- The application works offline for up to 30 days (grace period)

---

## Support

For assistance, contact your ChurnVision administrator.

---

## Technical Details

- **Docker Image:** {docker_image}
- **Tier:** {tenant.tier.value}
- **Max Employees:** {tenant.max_employees or "Unlimited"}
- **Max Users:** {tenant.max_users}
"""


def generate_installation_package(
    db: Session,
    tenant: Tenant,
    docker_image: str = "ghcr.io/riyadmehdi7/churnvision:latest",
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
