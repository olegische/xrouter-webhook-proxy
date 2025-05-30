"""Conversation webhook handlers."""
from typing import Dict

from agent.client import AgentClient
from api.adapters.carrot_quest_adapter import CarrotQuestWebhookAdapter
from api.models import WebhookRequest, WebhookStatus
from core.logger import LoggerService
from core.models.errors import ServiceError

from .base import BaseEventHandler


class ConversationEventHandler(BaseEventHandler):
    """Handler for chat message webhooks.

    Handles messages from chat (type=conversation).
    """

    def __init__(
        self,
        logger: LoggerService,
        agent_client: AgentClient,
    ) -> None:
        """Initialize handler.

        Args:
            logger: Logger service instance
            agent_client: Agent service client
        """
        super().__init__(logger, agent_client)
        self.adapter = CarrotQuestWebhookAdapter(logger)

    async def handle(self, event: WebhookRequest) -> Dict[str, str]:
        """Handle chat message webhook.

        Args:
            event: Webhook event data containing:
                - conversation: ConversationPart object with message details
                - user_id: ID of the user
                - user: User object

        Returns:
            Response data with status
        """
        if not event.conversation:
            self.logger.warning(
                "Missing conversation data in chat message webhook",
                extra={
                    "user_id": event.user_id,
                },
            )
            return {"status": WebhookStatus.IGNORED}

        # Log event processing
        self.logger.info(
            "Processing chat message webhook",
            extra={
                "conversation_id": event.conversation.conversation,
                "message_id": event.conversation.id,
                "user_id": event.user_id,
                "message_type": event.conversation.type,
                "direction": getattr(event.conversation, "direction", None),
            },
        )

        try:
            # Convert webhook to unified message using adapter
            message = await self.adapter.convert_to_message(event)

            if not message:
                self.logger.debug("Webhook did not contain a user message")
                return {"status": WebhookStatus.IGNORED}

            # Send message to agent service
            await self.agent_client.process_message(message)

            return {"status": WebhookStatus.ACCEPTED}

        except ServiceError as e:
            # Handle agent service errors separately
            if e.code == 503 or e.details.get("is_service_down", False):
                # Service is down - log as warning, not error
                self.logger.warning(
                    "Agent service unavailable - webhook processed but not forwarded",
                    extra={
                        "conversation_id": event.conversation.conversation,
                        "message_id": event.conversation.id,
                        "user_id": event.user_id,
                        "agent_service_url": self.agent_client.base_url,
                        "error_type": e.details.get("error_type", "unknown"),
                    },
                )
            else:
                # Other service errors - log as error with full details
                self.logger.error(
                    "Agent service error processing webhook",
                    extra={
                        "conversation_id": event.conversation.conversation,
                        "message_id": event.conversation.id,
                        "user_id": event.user_id,
                        "error": str(e),
                        "error_code": e.code,
                        "error_details": e.details,
                    },
                    exc_info=True,
                )
            # Return accepted to avoid webhook retries
            return {"status": WebhookStatus.ACCEPTED}

        except Exception as e:
            self.logger.error(
                "Failed to process conversation webhook",
                extra={
                    "conversation_id": event.conversation.conversation,
                    "message_id": event.conversation.id,
                    "user_id": event.user_id,
                    "error": str(e),
                },
                exc_info=True,
            )
            # Return accepted to avoid webhook retries
            return {"status": WebhookStatus.ACCEPTED}
