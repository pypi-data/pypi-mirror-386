# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from copy import copy
from typing import Self, TypeVar

from cachetools import Cache, LRUCache, TTLCache

from beeai_framework.cache.base import BaseCache

T = TypeVar("T")


class SlidingCache(BaseCache[T]):
    """Cache implementation using a sliding window strategy."""

    def __init__(self, size: int, ttl: float | None = None) -> None:
        super().__init__()
        self._ttl = ttl
        self._items: Cache[str, T] = TTLCache(maxsize=size, ttl=ttl) if ttl else LRUCache(maxsize=size)

    async def set(self, key: str, value: T) -> None:
        self._items[key] = value

    async def get(self, key: str) -> T | None:
        return self._items.get(key, default=None)

    async def has(self, key: str) -> bool:
        return key in self._items

    async def delete(self, key: str) -> bool:
        if not await self.has(key):
            return False

        self._items.pop(key)
        return True

    async def clear(self) -> None:
        self._items.clear()

    async def size(self) -> int:
        return len(self._items)

    async def clone(self) -> Self:
        cloned = type(self)(len(self._items), self._ttl)
        cloned._items = copy(self._items)
        return cloned
