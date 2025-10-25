"""Taskyto chatbot implementation."""

from dataclasses import dataclass
from typing import Any

from chatbot_connectors.core import (
    Chatbot,
    ChatbotConfig,
    EndpointConfig,
    Parameter,
    Payload,
    RequestMethod,
    ResponseProcessor,
)


class TaskytoResponseProcessor(ResponseProcessor):
    """Response processor for Taskyto chatbot."""

    def process(self, response_json: dict[str, Any] | list[dict[str, Any]]) -> str:
        """Extract the message from the Taskyto response JSON.

        Args:
            response_json: The JSON response from the API.

        Returns:
            The message string from the response.
        """
        if isinstance(response_json, list):
            return ""
        return response_json.get("message", "")


@dataclass
class TaskytoConfig(ChatbotConfig):
    """Configuration specific to Taskyto chatbot."""


class ChatbotTaskyto(Chatbot):
    """Connector for the Taskyto chatbot API."""

    def __init__(
        self,
        base_url: str,
        port: int = 5000,
        timeout: float | tuple[float, float] | None = 60,
    ) -> None:
        """Initialize the Taskyto chatbot connector.

        Args:
            base_url: The base URL for the Taskyto API.
            port: The port for the Taskyto API.
            timeout: Request timeout in seconds or (connect, read) tuple.
        """
        config = TaskytoConfig(base_url=f"{base_url}:{port}", timeout=timeout)
        super().__init__(config)

    @classmethod
    def get_chatbot_parameters(cls) -> list[Parameter]:
        """Return the parameters required to initialize this chatbot."""
        return [
            Parameter(
                name="base_url",
                type="string",
                required=True,
                description="The base URL of the Taskyto server.",
            ),
            Parameter(
                name="port",
                type="integer",
                required=False,
                description="The port of the Taskyto server.",
                default=5000,
            ),
        ]

    def get_endpoints(self) -> dict[str, EndpointConfig]:
        """Return endpoint configurations for Taskyto chatbot."""
        return {
            "new_conversation": EndpointConfig(
                path="/conversation/new", method=RequestMethod.POST, timeout=self.config.timeout
            ),
            "send_message": EndpointConfig(
                path="/conversation/user_message", method=RequestMethod.POST, timeout=self.config.timeout
            ),
        }

    def get_response_processor(self) -> ResponseProcessor:
        """Return the response processor for Taskyto chatbot."""
        return TaskytoResponseProcessor()

    def prepare_message_payload(self, user_msg: str) -> Payload:
        """Prepare the payload for sending a message to Taskyto.

        Args:
            user_msg: The user's message.

        Returns:
            Payload dictionary for the API request.
        """
        return {"id": self.conversation_id, "message": user_msg}
