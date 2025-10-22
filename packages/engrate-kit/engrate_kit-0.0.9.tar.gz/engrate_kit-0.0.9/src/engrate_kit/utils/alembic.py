import importlib.util
import sys
from pathlib import Path

from alembic import context
from alembic.config import Config
from sqlalchemy.engine.url import make_url
from sqlmodel import SQLModel

from .plugin import find_plugin_root, find_settings


def get_alembic_config() -> Config:
    """Load Alembic config from plugin root and inject DB_URL and script location."""
    root = find_plugin_root()

    ini_path = root / "alembic.ini"
    migrations_dir = root / "migrations"

    if not ini_path.exists():
        raise FileNotFoundError(f"No alembic.ini found in {root}")

    settings, _ = find_settings()

    cfg = Config(str(ini_path))
    cfg.set_main_option("sqlalchemy.url", to_sync_url(settings.DB_URL))
    cfg.set_main_option("script_location", str(migrations_dir))
    cfg.config_file_name = str(ini_path)

    return cfg


def to_sync_url(url: str) -> str:
    """We're using the default synchronous alembic env to make templating
    easier for now."""
    u = make_url(url)
    replacements = {
        "sqlite+aiosqlite": "sqlite",
        "postgresql+asyncpg": "postgresql+psycopg",
    }
    for k, v in replacements.items():
        if u.drivername.startswith(k):
            u = u.set(drivername=v)
            break
    return str(u)
