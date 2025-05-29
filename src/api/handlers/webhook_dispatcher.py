"""Webhook event dispatcher implementation."""
from typing import Dict

from api.models import WebhookRequest
from core.logger import LoggerService

from .factory import HandlerFactory


class WebhookDispatcher:
    """Universal dispatcher for webhook events from any source."""

    def __init__(
        self,
        logger: LoggerService,
        handler_factory: HandlerFactory,
    ) -> None:
        """Initialize dispatcher.

        Args:
            logger: Logger service instance
            handler_factory: Handler factory instance
        """
        self.logger = logger.get_logger(__name__)
        self.factory = handler_factory

    async def dispatch(self, event: WebhookRequest) -> Dict[str, str]:
        """Dispatch webhook event to appropriate handler.

        Args:
            event: Webhook event data

        Returns:
            Response data with status
        """
        handler = self.factory.create(event)
        return await handler.handle(event)
