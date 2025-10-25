"""RASA chatbot implementation."""

import uuid
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


class RasaResponseProcessor(ResponseProcessor):
    """Response processor for RASA chatbot."""

    def process(self, response_json: dict[str, Any] | list[dict[str, Any]]) -> str:
        """Process the RASA response JSON and extract messages.

        RASA returns a list of response objects, each potentially containing text,
        images, buttons, or other elements.

        Args:
            response_json: The JSON response from the RASA API (can be list or dict)

        Returns:
            Concatenated text from all response messages
        """
        messages = response_json if isinstance(response_json, list) else response_json.get("messages", [])

        if not isinstance(messages, list):
            return ""

        text_parts: list[str] = []
        for message in messages:
            if not isinstance(message, dict):
                continue

            self._extract_text_content(message, text_parts)
            self._extract_button_content(message, text_parts)
            self._extract_custom_content(message, text_parts)

        return "\n".join(text_parts) if text_parts else ""

    def _extract_text_content(self, message: dict[str, Any], text_parts: list[str]) -> None:
        """Extract text content from a message."""
        text = message.get("text")
        if isinstance(text, str):
            text_parts.append(text)

    def _extract_button_content(self, message: dict[str, Any], text_parts: list[str]) -> None:
        """Extract button content from a message."""
        buttons = message.get("buttons")
        if isinstance(buttons, list):
            button_texts: list[str] = []
            for btn in buttons:
                if isinstance(btn, dict):
                    title = btn.get("title") or btn.get("payload") or ""
                    if isinstance(title, str):
                        button_texts.append(title)
            if button_texts:
                text_parts.append(f"Options: {', '.join(button_texts)}")

    def _extract_custom_content(self, message: dict[str, Any], text_parts: list[str]) -> None:
        """Extract custom content from a message."""
        custom = message.get("custom")
        if custom is not None:
            text_parts.append(str(custom))


@dataclass
class RasaConfig(ChatbotConfig):
    """Configuration for RASA chatbot."""

    sender_id: str = "user"
    webhook_path: str = "/webhooks/rest/webhook"

    def __post_init__(self) -> None:
        """Set up headers after initialization."""
        self.headers = {"Content-Type": "application/json"}


class RasaChatbot(Chatbot):
    """Connector for RASA chatbot using REST webhook."""

    def __init__(
        self,
        base_url: str,
        sender_id: str = "user",
        timeout: float | tuple[float, float] | None = 60,
    ) -> None:
        """Initialize the RASA chatbot connector.

        Args:
            base_url: The base URL for the RASA server
            sender_id: Unique identifier for the conversation sender
            timeout: Request timeout in seconds or (connect, read) tuple
        """
        config = RasaConfig(base_url=base_url, sender_id=sender_id, timeout=timeout)
        super().__init__(config)
        self.rasa_config = config

    @classmethod
    def get_chatbot_parameters(cls) -> list[Parameter]:
        """Return the parameters required to initialize this chatbot."""
        return [
            Parameter(
                name="base_url",
                type="string",
                required=True,
                description="The base URL of the RASA server.",
            ),
            Parameter(
                name="sender_id",
                type="string",
                required=False,
                description="A unique identifier for the conversation sender.",
                default="user",
            ),
        ]

    def get_endpoints(self) -> dict[str, EndpointConfig]:
        """Return endpoint configurations for RASA chatbot."""
        return {
            "send_message": EndpointConfig(
                path=self.rasa_config.webhook_path,
                method=RequestMethod.POST,
                timeout=self.config.timeout,
            )
        }

    def get_response_processor(self) -> ResponseProcessor:
        """Return the response processor for RASA chatbot."""
        return RasaResponseProcessor()

    def prepare_message_payload(self, user_msg: str) -> Payload:
        """Prepare the payload for sending a message to RASA.

        Args:
            user_msg: The user's message

        Returns:
            Payload dictionary for the RASA webhook request
        """
        return {"sender": self.rasa_config.sender_id, "message": user_msg}

    def _requires_conversation_id(self) -> bool:
        """RASA uses sender_id for conversation tracking."""
        return False

    def create_new_conversation(self) -> bool:
        """Create a new conversation by generating a new sender ID."""
        self.rasa_config.sender_id = f"user_{uuid.uuid4().hex[:8]}"
        return True
