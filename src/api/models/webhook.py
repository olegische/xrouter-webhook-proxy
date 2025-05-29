"""Webhook models for API endpoints."""
from enum import Enum
from typing import Dict, Optional, Union

from pydantic import BaseModel, Field

from source.carrot_quest.models import WebhookEvent


class WebhookStatus(str, Enum):
    """Webhook response status enumeration."""

    ACCEPTED = "accepted"  # Webhook received and validation passed
    PROCESSING = "processing"  # Processing started (legacy)
    PROCESSED = "processed"  # Processing completed (legacy)
    IGNORED = "ignored"  # Event type not supported


class CarrotQuestWebhookRequest(WebhookEvent):
    """Webhook request model extending Carrot Quest webhook event."""


# Union type for all supported webhook requests
# Add new webhook request types here as they are implemented
WebhookRequest = Union[
    CarrotQuestWebhookRequest,
    # TelegramWebhookRequest,  # Future
    # SlackWebhookRequest,     # Future
]


class WebhookResponse(BaseModel):
    """Webhook response model."""

    status: WebhookStatus = Field(..., description="Processing status")
    details: Optional[Dict] = Field(None, description="Additional response details")
