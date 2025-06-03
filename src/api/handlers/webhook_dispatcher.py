"""Webhook event dispatcher implementation."""
from typing import Dict, Optional

from api.models import WebhookRequest, WebhookStatus
from core.logger import LoggerService
from core.settings import Settings
from source.carrot_quest.models import WebhookType
from source.carrot_quest.models.objects import ConversationPartType

from .factory import HandlerFactory


class WebhookDispatcher:
    """Universal dispatcher for webhook events from any source."""

    def __init__(
        self,
        logger: LoggerService,
        handler_factory: HandlerFactory,
        settings: Settings,
    ) -> None:
        """Initialize dispatcher.

        Args:
            logger: Logger service instance
            handler_factory: Handler factory instance
            settings: Application settings
        """
        self.logger = logger.get_logger(__name__)
        self.factory = handler_factory
        self.settings = settings

    def _get_user_id_from_event(self, event: WebhookRequest) -> Optional[str]:
        """Extract user ID from webhook event.

        For conversation events, user ID is in the conversation object.
        For other events, it's in the top-level user_id field.

        Args:
            event: Webhook event data

        Returns:
            User ID if found, None otherwise
        """
        # For conversation events, user ID is in the conversation object
        if hasattr(event, "type") and event.type == WebhookType.CONVERSATION:
            if hasattr(event, "conversation") and event.conversation:
                # Check if this is a user reply (not admin or system message)
                if (
                    hasattr(event.conversation, "type")
                    and event.conversation.type == ConversationPartType.REPLY_USER
                ):
                    # First try to get from 'from' field for user replies
                    if hasattr(event.conversation, "from_"):
                        return str(event.conversation.from_)
                    # Fallback to 'user' field if available
                    elif (
                        hasattr(event.conversation, "user") and event.conversation.user
                    ):
                        return str(event.conversation.user)

        # For other events, user ID is in the top-level field
        elif hasattr(event, "user_id") and event.user_id:
            return event.user_id

        return None

    async def dispatch(self, event: WebhookRequest) -> Dict[str, str]:
        """Dispatch webhook event to appropriate handler.

        Args:
            event: Webhook event data

        Returns:
            Response data with status
        """
        # Check if user whitelist filtering is enabled
        if self.settings.ENABLE_USER_WHITELIST and self.settings.WHITELIST_USERS:
            # Extract user ID from the event
            user_id = self._get_user_id_from_event(event)

            # If user ID is found and not in whitelist, ignore the webhook
            if user_id and user_id not in self.settings.WHITELIST_USERS:
                self.logger.info(
                    "User not in whitelist, ignoring webhook",
                    extra={
                        "user_id": user_id,
                        "webhook_type": getattr(event, "type", None),
                    },
                )
                return {"status": WebhookStatus.IGNORED}

        # Proceed with normal dispatch
        handler = self.factory.create(event)
        return await handler.handle(event)
