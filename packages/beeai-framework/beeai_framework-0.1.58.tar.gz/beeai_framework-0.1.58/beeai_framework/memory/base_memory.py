# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator
from typing import TYPE_CHECKING, Any, Self

from beeai_framework.backend.message import AnyMessage

if TYPE_CHECKING:
    from beeai_framework.memory.readonly_memory import ReadOnlyMemory


class BaseMemory(ABC):
    """Abstract base class for all memory implementations."""

    @property
    @abstractmethod
    def messages(self) -> list[AnyMessage]:
        """Return list of stored messages."""
        pass

    @abstractmethod
    async def add(self, message: AnyMessage, index: int | None = None) -> None:
        """Add a message to memory."""
        pass

    @abstractmethod
    async def delete(self, message: AnyMessage) -> bool:
        """Delete a message from memory."""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Clear all messages from memory."""
        pass

    async def add_many(self, messages: Iterable[AnyMessage], start: int | None = None) -> None:
        """Add multiple messages to memory."""
        for counter, msg in enumerate(messages):
            index = None if start is None else start + counter
            await self.add(msg, index)

    async def delete_many(self, messages: Iterable[AnyMessage]) -> None:
        """Delete multiple messages from memory."""
        for msg in messages:
            await self.delete(msg)

    async def splice(self, start: int, delete_count: int, *items: AnyMessage) -> list[AnyMessage]:
        """Remove and insert messages at a specific position."""
        total = len(self.messages)
        start = max(total + start, 0) if start < 0 else start
        delete_count = min(delete_count, total - start)

        deleted_items = self.messages[start : start + delete_count]
        await self.delete_many(deleted_items)
        await self.add_many(items, start)

        return deleted_items

    def is_empty(self) -> bool:
        """Check if memory is empty."""
        return len(self.messages) == 0

    def __iter__(self) -> Iterator[AnyMessage]:
        return iter(self.messages)

    def as_read_only(self) -> "ReadOnlyMemory":
        """Return a read-only view of this memory."""
        from beeai_framework.memory.readonly_memory import (  # Import here to avoid circular import
            ReadOnlyMemory,
        )

        return ReadOnlyMemory(self)

    async def clone(self) -> Self:
        return type(self)()

    def to_json_safe(self) -> dict[str, Any]:
        return {
            "name": type(self).__name__,
            "messages": self.messages,
        }
