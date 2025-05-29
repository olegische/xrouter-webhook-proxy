"""FastAPI dependencies for dependency injection."""
from typing import Annotated, cast

from fastapi import Depends, Request

from agent.client import AgentClient
from api.handlers.factory import HandlerFactory
from api.handlers.webhook_dispatcher import WebhookDispatcher
from api.services.carrot_quest_webhook_parser import CarrotQuestWebhookParser
from core.logger import LoggerService
from core.settings import Settings


def get_logger(request: Request) -> LoggerService:
    """Get logger service from app state.

    Args:
        request: FastAPI request object

    Returns:
        Logger service instance
    """
    return cast(LoggerService, request.app.state.logger)


def get_settings(request: Request) -> Settings:
    """Get settings from app state.

    Args:
        request: FastAPI request object

    Returns:
        Settings instance
    """
    return cast(Settings, request.app.state.settings)


def get_agent_client(request: Request) -> AgentClient:
    """Get agent client from app state.

    Args:
        request: FastAPI request object

    Returns:
        Agent client instance
    """
    return cast(AgentClient, request.app.state.agent_client)


def get_webhook_parser(
    logger: Annotated[LoggerService, Depends(get_logger)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> CarrotQuestWebhookParser:
    """Create webhook parser instance for request.

    Args:
        logger: Logger service instance
        settings: Settings instance

    Returns:
        Webhook parser instance
    """
    return CarrotQuestWebhookParser(logger=logger, settings=settings)


def get_handler_factory(request: Request) -> HandlerFactory:
    """Get handler factory from app state.

    Args:
        request: FastAPI request object

    Returns:
        Handler factory instance
    """
    return cast(HandlerFactory, request.app.state.handler_factory)


def get_webhook_dispatcher(
    logger: Annotated[LoggerService, Depends(get_logger)],
    handler_factory: Annotated[HandlerFactory, Depends(get_handler_factory)],
) -> WebhookDispatcher:
    """Create webhook dispatcher instance for request.

    Args:
        logger: Logger service instance
        handler_factory: Handler factory instance

    Returns:
        Webhook dispatcher instance
    """
    return WebhookDispatcher(
        logger=logger,
        handler_factory=handler_factory,
    )
