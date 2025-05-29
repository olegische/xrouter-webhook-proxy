"""CarrotQuest webhook adapter."""
from datetime import datetime
from typing import Optional

from api.models.message import InputMessage, Message, MessageRole, MessageSource
from api.models.webhook import CarrotQuestWebhookRequest
from core.logger import LoggerService
from source.carrot_quest.models import DirectionType, WebhookType


class CarrotQuestWebhookAdapter:
    """Webhook adapter for CarrotQuest system."""

    def __init__(self, logger: LoggerService) -> None:
        """Initialize CarrotQuest adapter.

        Args:
            logger: Logger service instance
        """
        self.logger = logger.get_logger(self.__class__.__name__)

    async def convert_to_message(
        self, webhook_request: CarrotQuestWebhookRequest
    ) -> Optional[Message]:
        """Convert CarrotQuest webhook request into a unified Message.

        Args:
            webhook_request: Already parsed and validated webhook request

        Returns:
            Converted Message object or None if not a user message

        Raises:
            ValueError: If data cannot be converted to Message
        """
        try:
            # Only process conversation webhooks (actual chat messages)
            if webhook_request.type != WebhookType.CONVERSATION:
                self.logger.debug(
                    "Ignoring non-conversation webhook",
                    extra={"webhook_type": webhook_request.type},
                )
                return None

            # Check if conversation data exists
            if not webhook_request.conversation:
                self.logger.warning("Missing conversation data in webhook")
                return None

            conversation = webhook_request.conversation

            # Extract message details from parsed objects
            message_id = str(conversation.id)
            thread_id = str(conversation.conversation)
            user_id = str(webhook_request.user_id)
            content = str(conversation.body)
            timestamp = datetime.fromtimestamp(conversation.created)

            # Determine message role based on direction
            role = MessageRole.USER
            if (
                hasattr(conversation, "direction")
                and conversation.direction == DirectionType.ADMIN_TO_USER
            ):
                role = MessageRole.ASSISTANT

            # Extract channel information
            channel_type = None
            if hasattr(conversation, "type"):
                channel_type = str(conversation.type)

            # Build source context (may contain personal data for debugging)
            source_context = {
                "webhook_type": webhook_request.type,
                "conversation_part_type": getattr(conversation, "type", None),
                "sent_via": getattr(conversation, "sent_via", None),
                "direction": getattr(conversation, "direction", None),
                "user_data": webhook_request.user.model_dump()
                if webhook_request.user
                else {},
                "raw_webhook": webhook_request.model_dump(),
            }

            # Create input message following OpenAI format
            input_message = InputMessage(role=role, content=content)

            # Create unified message
            message = Message(
                input=[input_message],
                message_id=message_id,
                thread_id=thread_id,
                user_id=user_id,
                source=MessageSource.CARROT_QUEST,
                source_message_id=message_id,
                timestamp=timestamp,
                channel_type=channel_type,
                source_context=source_context,
            )

            self.logger.info(
                "Converted CarrotQuest webhook to message",
                extra={
                    "message_id": message_id,
                    "thread_id": thread_id,
                    "user_id": user_id,
                    "role": role,
                    "content_length": len(content),
                },
            )

            return message

        except Exception as e:
            self.logger.error(
                "Failed to convert CarrotQuest webhook to message",
                extra={"error": str(e), "webhook_type": webhook_request.type},
                exc_info=True,
            )
            raise ValueError(
                f"Failed to convert CarrotQuest webhook to message: {str(e)}"
            )
