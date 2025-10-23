# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod
from agntcy_app_sdk.protocols.message import Message
from typing import Callable, Optional
from typing import Any, TypeVar, Type
import asyncio

from enum import Enum, auto


class ResponseMode(Enum):
    """Defines how responses to a topic request should be handled."""

    FIRST = auto()
    """First-response-wins. Return as soon as the first reply arrives."""

    COLLECT_N = auto()
    """Collect N responses from a topic, then return (or until timeout)."""

    COLLECT_ALL = auto()
    """Collect all available responses (requires known member list)."""

    GROUP = auto()
    """Respond to a group of subscribers."""


T = TypeVar("T", bound="BaseTransport")


class BaseTransport(ABC):
    """
    Abstract base class for transport protocols.
    This class defines the interface for different transport protocols
    such as SLIM, NATS, MQTT, KAFKA, etc.
    """

    @classmethod
    @abstractmethod
    def from_client(cls: Type[T], client: Any, name: str = None) -> T:
        """Create a transport instance from a client."""
        pass

    @classmethod
    @abstractmethod
    def from_config(cls: Type[T], endpoint: str, name: str = None, **kwargs) -> T:
        """Create a transport instance from a configuration."""
        pass

    @abstractmethod
    def type(self) -> str:
        """Return the transport type."""
        pass

    @abstractmethod
    async def setup(self, **kwargs) -> None:
        """Perform any necessary setup for the transport, useful for async initialization."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the transport connection."""
        pass

    @abstractmethod
    async def publish(
        self,
        topic: str,
        message: Message,
    ) -> None:
        """Publish a message to a topic, fire and forget."""
        pass

    @abstractmethod
    async def request(
        self,
        topic: str,
        message: Message,
        response_mode: ResponseMode = ResponseMode.FIRST,
        timeout: Optional[float] = 60.0,
        **kwargs,
    ) -> Optional[Message]:
        """Publish with expectation of replies, governed by ResponseMode."""

    @abstractmethod
    async def subscribe(self, topic: str, callback: callable = None) -> None:
        """Subscribe to a topic with a callback."""
        pass

    @abstractmethod
    def set_callback(self, handler: Callable[[Message], asyncio.Future]) -> None:
        """Set the message handler function."""
        pass
