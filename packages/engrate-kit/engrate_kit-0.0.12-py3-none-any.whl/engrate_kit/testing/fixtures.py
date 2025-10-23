import importlib

import pytest
from alembic import command
from fastapi.testclient import TestClient
from fastmcp.client import Client as MCPClient
from fastmcp.client.transports import FastMCPTransport

from engrate_kit.utils.alembic import get_alembic_config


@pytest.fixture()
def db_file(tmp_path_factory):
    """Create temporary db file."""
    return tmp_path_factory.mktemp("data") / "test.db"


@pytest.fixture(autouse=True)
def set_up_db(monkeypatch, db_file):
    """Run Alembic migrations before any test."""
    db_url_async = f"sqlite+aiosqlite:///{db_file}"
    db_url_sync = f"sqlite:///{db_file}"
    monkeypatch.setenv("DB_URL", db_url_async)
    alembic_cfg = get_alembic_config()
    alembic_cfg.set_main_option("sqlalchemy.url", db_url_sync)
    command.upgrade(alembic_cfg, "head")
    yield


def _import_app(module_name: str):
    """Dynamically import app from app module."""
    mod = importlib.import_module(f"{module_name}.app")
    return mod.create_app()


@pytest.fixture
def client(request):
    """Inject a FastAPI test client."""
    app_module_name = getattr(request.config, "app_module_name", "plugin")
    app = _import_app(app_module_name)
    with TestClient(app) as c:
        yield c


@pytest.fixture
def mcp_client(request):
    """Inject an MCP test client."""
    app_module_name = getattr(request.config, "app_module_name", "plugin")
    app = _import_app(app_module_name)
    assert app.mcp_server is not None
    return MCPClient(transport=FastMCPTransport(app.mcp_server))
