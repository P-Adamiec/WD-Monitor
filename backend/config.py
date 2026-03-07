"""Configuration module — loads environment variables with .env fallback.
Docker-compose values override .env file values (standard Docker behavior).
"""
import os

# Load .env file if it exists (docker-compose env vars take priority)
def _load_dotenv():
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                key, _, value = line.partition('=')
                key, value = key.strip(), value.strip().strip('"').strip("'")
                # Only set if not already defined (docker-compose overrides .env)
                if key not in os.environ:
                    os.environ[key] = value

_load_dotenv()

# Database
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://monitor_user:monitor_password@db:5432/monitor_db")

# Monitoring
CHECK_INTERVAL_SECONDS = int(os.environ.get("CHECK_INTERVAL_SECONDS", 60))
DEFAULT_LOCALE = os.environ.get("WD_LOCALE", "pl-pl")

# Catalog
CATALOG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "catalog.json")
CATALOG_REFRESH_INTERVAL = int(os.environ.get("CATALOG_REFRESH_HOURS", 24)) * 3600
