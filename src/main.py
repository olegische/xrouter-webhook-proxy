"""Panda AI FastAPI application entry point."""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI

from agent.client import AgentClient
from api.handlers.factory import HandlerFactory
from app import WebhookApp
from core.logger import LoggerService
from core.settings import settings


@asynccontextmanager
async def lifespan(app: WebhookApp) -> AsyncGenerator[None, None]:
    """Manage application lifespan.

    This function handles startup and shutdown events for the application.

    Args:
        app: FastAPI application instance

    Yields:
        None
    """
    app_logger = app.state.logger.get_logger(__name__)
    app_logger.info("Application configured successfully")

    try:
        yield
    finally:
        app_logger.info("Shutting down application")

        # Close agent client
        if hasattr(app.state, "agent_client"):
            await app.state.agent_client.close()
            app_logger.info("Agent client closed")


def init_app() -> FastAPI:
    """Initialize FastAPI application."""
    # Create the app with lifespan
    app = WebhookApp(lifespan=lifespan)

    # Initialize singleton services
    logger = LoggerService(settings_instance=settings)
    agent_client = AgentClient(settings=settings, logger=logger)
    handler_factory = HandlerFactory(
        logger=logger,
        agent_client=agent_client,
        settings=settings,
    )

    # Set dependencies on app state
    app.state.logger = logger
    app.state.settings = settings
    app.state.agent_client = agent_client
    app.state.handler_factory = handler_factory

    # Configure the application
    app.configure()

    return app


# Initialize application at the module level for uvicorn
def get_app() -> FastAPI:
    """Factory function to create the FastAPI app."""
    return init_app()


if __name__ == "__main__":
    app = init_app()

    # Get host and port from environment variables
    host = settings.HOST
    port = int(settings.PORT)

    # Run server
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=True,
    )
