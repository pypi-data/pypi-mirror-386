"""Core classes and interfaces for chatbot connectors."""

import json
from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal, TypeAlias
from urllib.parse import urljoin

import requests
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from chatbot_connectors.exceptions import (
    ConnectorAuthenticationError,
    ConnectorConnectionError,
    ConnectorResponseError,
)
from chatbot_connectors.logging_utils import get_logger

logger = get_logger()

# Type aliases
ChatbotResponse = tuple[bool, str | None]
Headers = dict[str, str]
Payload = dict[str, Any]
JsonSerializable: TypeAlias = dict[str, "JsonSerializable"] | list["JsonSerializable"] | str | int | float | bool | None


def _make_resilient_session() -> Session:
    """Create a requests session configured with retry and pooling defaults."""
    retry = Retry(
        total=4,
        connect=3,
        read=3,
        status=3,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        respect_retry_after_header=True,
        allowed_methods={"GET", "HEAD", "OPTIONS", "POST"},
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=20, pool_maxsize=50)

    session = Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def _normalize_timeout(timeout: float | Sequence[float] | None) -> tuple[float, float]:
    """Normalize a timeout value into a (connect, read) tuple."""
    if timeout is None:
        return (5.0, 60.0)
    if isinstance(timeout, (int, float)):
        value = float(timeout)
        return (value, value)
    if isinstance(timeout, Sequence):
        if isinstance(timeout, (str, bytes)):
            error_msg = "Timeout sequence must be a tuple/list of numeric values, not a string"
            raise TypeError(error_msg)
        timeout_length = 2
        if len(timeout) != timeout_length:
            error_msg = "Timeout sequence must contain exactly two numeric values"
            raise ValueError(error_msg)
        connect, read = timeout
        return (float(connect), float(read))
    error_msg = f"Unsupported timeout type: {type(timeout)!r}"
    raise TypeError(error_msg)


@dataclass
class Parameter:
    """A parameter for a chatbot connector."""

    name: str
    type: Literal["string", "integer", "boolean"]
    required: bool
    description: str
    default: Any = None


class RequestMethod(Enum):
    """Supported HTTP methods."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"


@dataclass
class EndpointConfig:
    """Configuration for API endpoints."""

    path: str
    method: RequestMethod = RequestMethod.POST
    headers: Headers = field(default_factory=dict)
    timeout: float | Sequence[float] | None = 60


@dataclass
class ChatbotConfig:
    """Base configuration for chatbot connectors."""

    base_url: str
    timeout: float | Sequence[float] | None = 60
    fallback_message: str = "I do not understand you"
    headers: Headers = field(default_factory=dict)

    def get_full_url(self, endpoint: str) -> str:
        """Construct full URL from base URL and endpoint."""
        return urljoin(self.base_url, endpoint.lstrip("/"))


class ResponseProcessor(ABC):
    """Abstract base class for processing chatbot responses."""

    @abstractmethod
    def process(self, response_json: dict[str, Any] | list[dict[str, Any]]) -> str:
        """Process the JSON response and extract meaningful text.

        Args:
            response_json: The JSON response from the API (dict or list)

        Returns:
            Processed response text
        """


class SimpleTextProcessor(ResponseProcessor):
    """Simple processor that extracts text from a specified field."""

    def __init__(self, text_field: str = "message") -> None:
        """Initialize the processor with the field to extract text from.

        Args:
            text_field: The field name to extract text from in the response JSON.
        """
        self.text_field = text_field

    def process(self, response_json: dict[str, Any] | list[dict[str, Any]]) -> str:
        """Extract text from the specified field in the response JSON.

        Args:
            response_json: The JSON response from the API.

        Returns:
            Extracted text from the specified field, or an empty string if not found.
        """
        if isinstance(response_json, list):
            # If it's a list, try to get the first item
            if response_json and isinstance(response_json[0], dict):
                return response_json[0].get(self.text_field, "")
            return ""
        return response_json.get(self.text_field, "")


class Chatbot(ABC):
    """Abstract base class for chatbot connectors with common functionality."""

    def __init__(self, config: ChatbotConfig) -> None:
        """Initialize the chatbot connector.

        Args:
            config: The configuration for the chatbot connector.
        """
        self.config = config
        self.session = _make_resilient_session()
        self.conversation_id: str | None = None
        self._setup_session()

    @classmethod
    @abstractmethod
    def get_chatbot_parameters(cls) -> list[Parameter]:
        """Return the parameters required to initialize this chatbot."""

    def _setup_session(self) -> None:
        """Set up the requests session with default headers."""
        self.session.headers.update(self.config.headers)

    def _resolve_timeout(self, timeout: float | Sequence[float] | None) -> tuple[float, float]:
        """Return a (connect, read) timeout tuple using connector defaults."""
        chosen_timeout = timeout if timeout is not None else self.config.timeout
        return _normalize_timeout(chosen_timeout)

    def health_check(self) -> None:
        """Performs a health check on a given endpoint to ensure connectivity.

        This method provides fail-early detection of connector issues including
        connectivity, authentication, and configuration problems.

        Raises:
            ConnectorConnectionError: If unable to connect to the endpoint
            ConnectorAuthenticationError: If authentication fails
            ConnectorResponseError: If the endpoint returns an invalid response
            ConnectorConfigurationError: If the connector configuration is invalid
        """
        endpoints = self.get_endpoints()
        health_check_endpoint = endpoints.get("health_check")

        if not health_check_endpoint:
            logger.debug("No health check endpoint available for %s connector", self.__class__.__name__)
            return

        url = self.config.get_full_url(health_check_endpoint.path)
        logger.info("Performing health check on %s", url)

        try:
            self._make_request(url, health_check_endpoint, {})
            logger.info("Health check passed for %s", url)

        except requests.exceptions.Timeout as exc:
            raise ConnectorConnectionError(
                connector_type=self.__class__.__name__,
                url=url,
                message=f"Timeout connecting to chatbot endpoint at {url}",
            ) from exc

        except requests.exceptions.ConnectionError as exc:
            raise ConnectorConnectionError(
                connector_type=self.__class__.__name__,
                url=url,
                message=f"Failed to connect to chatbot endpoint at {url}",
                original_error=exc,
            ) from exc

        except requests.exceptions.HTTPError as exc:
            status_code = exc.response.status_code
            if status_code in {401, 403}:
                raise ConnectorAuthenticationError(
                    connector_type=self.__class__.__name__,
                    url=url,
                    status_code=status_code,
                    response_text=exc.response.text,
                ) from exc
            raise ConnectorResponseError(
                connector_type=self.__class__.__name__,
                url=url,
                status_code=status_code,
                message=f"HTTP error from chatbot endpoint (HTTP {status_code})",
                response_text=exc.response.text,
            ) from exc

        except json.JSONDecodeError as exc:
            raise ConnectorResponseError(
                connector_type=self.__class__.__name__,
                url=url,
                message="Invalid response format from chatbot endpoint",
                original_error=exc,
            ) from exc

        except requests.RequestException as exc:
            raise ConnectorConnectionError(
                connector_type=self.__class__.__name__,
                url=url,
                message=f"Request failed for chatbot endpoint: {exc.__class__.__name__}",
                original_error=exc,
            ) from exc

    @abstractmethod
    def get_endpoints(self) -> dict[str, EndpointConfig]:
        """Return endpoint configurations for this chatbot.

        Returns:
            Dictionary mapping endpoint names to their configurations
        """

    @abstractmethod
    def get_response_processor(self) -> ResponseProcessor:
        """Return the response processor for this chatbot."""

    @abstractmethod
    def prepare_message_payload(self, user_msg: str) -> Payload:
        """Prepare the payload for sending a message.

        Args:
            user_msg: The user's message

        Returns:
            Payload dictionary for the API request
        """

    def create_new_conversation(self) -> bool:
        """Create a new conversation.

        Default implementation that can be overridden by subclasses.

        Returns:
            True if successful, False otherwise
        """
        endpoints = self.get_endpoints()
        if "new_conversation" not in endpoints:
            # If no new conversation endpoint, just reset the conversation ID
            self.conversation_id = None
            return True

        endpoint_config = endpoints["new_conversation"]
        url = self.config.get_full_url(endpoint_config.path)

        try:
            response = self._make_request(url, endpoint_config, {})
        except requests.RequestException as e:
            logger.exception(
                "Failed to create new conversation for %s at %s",
                self.__class__.__name__,
                url,
            )
            msg = f"Failed to create new conversation for {self.__class__.__name__} at {url}"
            raise ConnectorConnectionError(msg, original_error=e) from e
        else:
            if response:
                # Try to extract conversation ID if provided
                self.conversation_id = response.get("id") or response.get("conversation_id")
                return True
            # Response was empty but request succeeded
            return False

    def execute_with_input(self, user_msg: str) -> ChatbotResponse:
        """Send a message to the chatbot and get the response.

        Args:
            user_msg: The user's message

        Returns:
            Tuple of (success, response_text)
        """
        # Ensure we have a conversation if needed
        if self.conversation_id is None and self._requires_conversation_id() and not self.create_new_conversation():
            return False, "Failed to initialize conversation"

        endpoints = self.get_endpoints()
        if "send_message" not in endpoints:
            return False, "Send message endpoint not configured"

        endpoint_config = endpoints["send_message"]
        url = self.config.get_full_url(endpoint_config.path)
        payload = self.prepare_message_payload(user_msg)

        try:
            response_json = self._make_request(url, endpoint_config, payload)
        except requests.RequestException as e:
            logger.exception("Chatbot request failed for %s", self.__class__.__name__)
            msg = f"Chatbot request failed for {self.__class__.__name__} at {url}"
            raise ConnectorConnectionError(msg, original_error=e) from e

        if response_json:
            processor = self.get_response_processor()
            response_text = processor.process(response_json)
            return True, response_text

        return False, "No response received"

    def _requires_conversation_id(self) -> bool:
        """Check if this chatbot requires a conversation ID.

        Can be overridden by subclasses.
        """
        return True

    def _make_request(self, url: str, endpoint_config: EndpointConfig, payload: Payload) -> dict[str, Any] | None:
        """Make an HTTP request with error handling.

        Args:
            url: The request URL
            endpoint_config: Endpoint configuration
            payload: Request payload

        Returns:
            JSON response or None if failed
        """
        headers = {**self.session.headers, **endpoint_config.headers}
        timeout = self._resolve_timeout(endpoint_config.timeout)
        if endpoint_config.method == RequestMethod.GET:
            response = self.session.get(url, params=payload, headers=headers, timeout=timeout)
        else:
            response = self.session.request(
                endpoint_config.method.value,
                url,
                json=payload,
                headers=headers,
                timeout=timeout,
            )

        response.raise_for_status()
        return response.json()
