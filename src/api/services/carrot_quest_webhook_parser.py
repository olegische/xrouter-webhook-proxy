"""Webhook request parsing service."""
import json
from typing import Any, Dict

from fastapi import Request

from api.models import CarrotQuestWebhookRequest
from core.logger import LoggerService
from core.models.errors import ServiceError
from core.settings import Settings
from source.carrot_quest.models import Event, User, WebhookType
from source.carrot_quest.models.objects import ConversationPart


class CarrotQuestWebhookParser:
    """Service for parsing webhook request data."""

    def __init__(self, logger: LoggerService, settings: Settings) -> None:
        """Initialize parser.

        Args:
            logger: Logger service instance for logging
            settings: Application settings
        """
        self.logger = logger.get_logger(__name__)
        self.settings = settings

    def _validate_token(self, token: str) -> bool:
        """Validate webhook token.

        Args:
            token: Token from webhook request

        Returns:
            True if token matches configured token
        """
        return token == self.settings.CARROT_QUEST_WEBHOOK_TOKEN

    def _parse_required_fields(self, form_data: dict) -> Dict[str, Any]:
        """Parse required fields from form data.

        Args:
            form_data: Form data from request

        Returns:
            Dictionary with required fields
        """
        return {
            "type": WebhookType(str(form_data["type"])),
            "token": str(form_data["token"]),
        }

    def _parse_optional_fields(self, form_data: dict) -> Dict[str, Any]:
        """Parse optional string fields from form data.

        Args:
            form_data: Form data from request

        Returns:
            Dictionary with optional fields
        """
        optional_fields = {}
        for field in [
            "event_name",
            "event_id",
            "message_id",
            "sending_id",
            "message_name",
            "user_id",
        ]:
            if field in form_data:
                optional_fields[field] = str(form_data[field])

        # Parse user object if present
        if "user" in form_data:
            optional_fields["user"] = User(**json.loads(str(form_data["user"])))

        return optional_fields

    def _parse_nested_objects(self, form_data: dict) -> Dict[str, Any]:
        """Parse optional nested objects from form data.

        Args:
            form_data: Form data from request

        Returns:
            Dictionary with nested objects
        """
        nested_objects = {}
        if "event" in form_data:
            nested_objects["event"] = Event(**json.loads(str(form_data["event"])))
        if "conversation" in form_data:
            nested_objects["conversation"] = ConversationPart(
                **json.loads(str(form_data["conversation"]))
            )
        return nested_objects

    async def parse_request(self, request: Request) -> CarrotQuestWebhookRequest:
        """Parse webhook request data.

        Args:
            request: FastAPI request object

        Returns:
            Validated webhook request data

        Raises:
            ServiceError: If request data is invalid
        """
        try:
            # Parse form data
            form_data = await request.form()

            # Log form data for debugging
            form_dict = {key: str(value) for key, value in form_data.items()}
            self.logger.info(
                "Webhook form data received",
                extra={
                    "request_id": getattr(request.state, "request_id", None),
                    "form_keys": list(form_dict.keys()),
                    "form_data": form_dict,
                },
            )

            # Parse and validate required fields
            required_fields = self._parse_required_fields(form_data)

            # Validate webhook token
            if not self._validate_token(required_fields["token"]):
                self.logger.warning(
                    "Invalid webhook token",
                    extra={
                        "request_id": getattr(request.state, "request_id", None),
                        "client": request.client.host if request.client else None,
                    },
                )
                raise ServiceError(
                    code=401,
                    message="Invalid webhook token",
                    details={"field": "token"},
                )

            # Build webhook data dictionary
            webhook_data_dict = {}
            webhook_data_dict.update(required_fields)
            webhook_data_dict.update(self._parse_optional_fields(form_data))
            webhook_data_dict.update(self._parse_nested_objects(form_data))

            # Validate entire structure with Pydantic
            return CarrotQuestWebhookRequest(**webhook_data_dict)

        except Exception as e:
            self.logger.error(
                "Invalid request payload",
                extra={
                    "request_id": getattr(request.state, "request_id", None),
                    "error": str(e),
                },
            )
            raise ServiceError(
                code=400,
                message="Invalid request payload",
                details={"error": str(e)},
            )
