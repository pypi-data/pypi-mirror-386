import pytest
from alembic import command
from engrate_kit.utils.alembic import get_alembic_config
from fastapi.testclient import TestClient
from fastmcp.client import Client as MCPClient
from fastmcp.client.transports import FastMCPTransport


@pytest.fixture()
def db_file(tmp_path_factory):
    """Create temporary db file."""
    return tmp_path_factory.mktemp("data") / "test.db"


@pytest.fixture(autouse=True)
def set_up_db(monkeypatch):
    """Run Alembic migrations before any test."""
    db_url_async = f"sqlite+aiosqlite:///{db_file}"
    db_url_sync = f"sqlite:///{db_file}"
    monkeypatch.setenv("DB_URL", db_url_async)
    alembic_cfg = get_alembic_config()
    alembic_cfg.set_main_option("sqlalchemy.url", db_url_sync)
    command.upgrade(alembic_cfg, "head")
    yield


@pytest.fixture
def client():
    """Inject a FastAPI test client."""
    from {{app_module_name}}.app import create_app
    app = create_app()

    with TestClient(app) as c:
        yield c


@pytest.fixture
def mcp_client():
    """Inject a FastAPI test client."""
    from {{app_module_name}}.app import create_app
    app = create_app()

    assert app.mcp_server is not None
    return MCPClient(transport=FastMCPTransport(app.mcp_server))
