"""Agent service client."""
from typing import Any, Dict, Optional, cast

import httpx
from pydantic import ValidationError

from api.models.message import Message
from core.logger import LoggerService
from core.models.errors import ServiceError
from core.settings import Settings


class AgentClient:
    """Client for Agent service."""

    def __init__(self, settings: Settings, logger: LoggerService) -> None:
        """Initialize client.

        Args:
            settings: Application settings
            logger: Logger service
        """
        self.settings = settings
        self.base_url = settings.AGENT_SERVICE_URL
        self.timeout = settings.AGENT_SERVICE_TIMEOUT
        self.logger = logger.get_logger(__name__)
        self.client = self._create_client()

    def _create_client(self) -> httpx.AsyncClient:
        """Create and configure HTTP client.

        Returns:
            Configured HTTP client
        """
        return httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Content-Type": "application/json",
            },
            timeout=self.timeout,
        )

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make HTTP request to Agent service.

        Args:
            method: HTTP method
            endpoint: API endpoint
            json_data: JSON data to send
            params: Query parameters

        Returns:
            Response data

        Raises:
            ServiceError: If request fails
        """
        try:
            response = await self.client.request(
                method=method,
                url=endpoint,
                json=json_data,
                params=params,
            )
            response.raise_for_status()
            return cast(Dict[str, Any], response.json())
        except httpx.HTTPError as e:
            error_msg = str(e)
            status_code = 500
            response_data = None

            # Extract response data if available
            if hasattr(e, "response") and e.response is not None:
                status_code = e.response.status_code
                try:
                    response_data = e.response.json()
                    if isinstance(response_data, dict) and "error" in response_data:
                        error_msg = response_data["error"]
                except Exception:
                    try:
                        response_data = {"text": e.response.text[:500]}
                    except Exception:
                        response_data = {"text": "Unable to extract response text"}

            # Create error details
            details = {
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
            }

            if response_data:
                details["response_data"] = response_data

            if json_data:
                details["request_data"] = json_data

            raise ServiceError(
                code=status_code,
                message=f"Agent service request failed: {error_msg}",
                details=details,
            )

    async def process_message(self, message: Message) -> Dict[str, Any]:
        """Process message through agent service.

        Args:
            message: Unified message to process

        Returns:
            Processing result

        Raises:
            ServiceError: If processing fails
        """
        self.logger.debug(
            "Sending message to agent service",
            extra={
                "message_id": message.message_id,
                "thread_id": message.thread_id,
                "source": message.source,
                "user_id": message.user_id,
            },
        )

        try:
            response_data = await self._make_request(
                "POST",
                "/message",
                json_data=message.model_dump(exclude_none=True),
            )

            self.logger.info(
                "Message processed by agent service",
                extra={
                    "message_id": message.message_id,
                    "thread_id": message.thread_id,
                    "response_status": response_data.get("status", "unknown"),
                },
            )

            return response_data

        except ValidationError as e:
            raise ServiceError(
                code=400,
                message="Invalid agent service response format",
                details={"validation_errors": str(e)},
            )
        except ServiceError as e:
            new_error = ServiceError(
                code=e.code,
                message=f"Message processing failed: {e.message}",
                details={
                    "message_id": message.message_id,
                    "thread_id": message.thread_id,
                    **e.details,
                },
            )
            raise new_error from e

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()
