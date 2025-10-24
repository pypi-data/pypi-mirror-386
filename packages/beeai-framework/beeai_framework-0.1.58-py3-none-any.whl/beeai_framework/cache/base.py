# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod
from collections import OrderedDict
from hashlib import sha512
from typing import Any, Generic, Self, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class BaseCache(ABC, Generic[T]):
    """Abstract base class for all Cache implementations."""

    def __init__(self) -> None:
        super().__init__()
        self._enabled: bool = True

    @property
    def enabled(self) -> bool:
        return self._enabled

    @abstractmethod
    async def size(self) -> int:
        pass

    @abstractmethod
    async def set(self, key: str, value: T) -> None:
        pass

    @abstractmethod
    async def get(self, key: str) -> T | None:
        pass

    @abstractmethod
    async def has(self, key: str) -> bool:
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        pass

    @abstractmethod
    async def clear(self) -> None:
        pass

    @staticmethod
    def generate_key(*args: dict[str, Any] | BaseModel) -> str:
        cache_key_dict: dict[str, Any] = {}
        for arg in args:
            arg = arg or {}
            arg_dict = arg if isinstance(arg, dict) else arg.model_dump(exclude_none=True)
            cache_key_dict |= arg_dict

        cache_key_dict = OrderedDict(sorted(cache_key_dict.items()))
        cache_key_str = str(cache_key_dict).encode("utf-8", errors="ignore")
        return str(int.from_bytes(sha512(cache_key_str).digest()))

    async def clone(self) -> Self:
        cloned = type(self)()
        return cloned
