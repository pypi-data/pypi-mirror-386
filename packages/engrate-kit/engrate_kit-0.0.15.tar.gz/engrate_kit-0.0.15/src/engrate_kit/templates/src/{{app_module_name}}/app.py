from engrate_kit.core.app import App

from .conf import settings
from .mcp.health_server import server as health_server
from .routers.health_router import router as health_router


def create_app():
    app = App(settings=settings)

    app.include_router(health_router)
    app.include_mcp_server(health_server)

    return app


app = create_app()
