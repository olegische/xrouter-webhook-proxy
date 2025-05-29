"""Factory for creating webhook handlers."""
from agent.client import AgentClient
from api.models import CarrotQuestWebhookRequest, WebhookRequest
from core.logger import LoggerService
from core.models.errors import ValidationError
from core.settings import Settings
from source.carrot_quest.models import WebhookType

from .base import BaseEventHandler
from .conversation import ConversationEventHandler


class HandlerFactory:
    """Factory for creating webhook handlers."""

    def __init__(
        self,
        logger: LoggerService,
        agent_client: AgentClient,
        settings: Settings,
    ) -> None:
        """Initialize factory.

        Args:
            logger: Logger service instance
            agent_client: Agent service client
            settings: Application settings
        """
        self.logger = logger
        self.agent_client = agent_client
        self.settings = settings

    def create(self, event: WebhookRequest) -> BaseEventHandler:
        """Create appropriate handler for webhook event.

        Args:
            event: Webhook event data from any supported source

        Returns:
            Handler instance for the event

        Raises:
            ValidationError: If event type is not supported or event data is invalid
        """
        # Determine source and create appropriate handler
        if isinstance(event, CarrotQuestWebhookRequest):
            # CarrotQuest webhook - check if it's a conversation
            if event.type == WebhookType.CONVERSATION:
                if not event.conversation:
                    raise ValidationError(
                        message="Missing conversation data",
                        field="conversation",
                    )

                return ConversationEventHandler(
                    logger=self.logger,
                    agent_client=self.agent_client,
                )
            else:
                raise ValidationError(
                    message=(
                        f"Unsupported CarrotQuest webhook type: {event.type}. "
                        "Only CONVERSATION webhooks are supported."
                    ),
                    field="type",
                )

        # Future: Add support for other webhook sources
        # elif isinstance(event, TelegramWebhookRequest):
        #     return ConversationEventHandler(...)
        # elif isinstance(event, SlackWebhookRequest):
        #     return ConversationEventHandler(...)

        # Unknown webhook source
        raise ValidationError(
            message=f"Unsupported webhook source: {type(event).__name__}",
            field="source",
        )
