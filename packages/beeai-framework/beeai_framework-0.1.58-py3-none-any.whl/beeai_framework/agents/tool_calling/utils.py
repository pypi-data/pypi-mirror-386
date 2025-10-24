# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from pydantic import BaseModel

from beeai_framework.backend import MessageToolCallContent
from beeai_framework.utils.counter import OccurrencesCounter


class ToolCallCheckerConfig(BaseModel):
    max_strike_length: int = 1
    max_total_occurrences: int = 5
    window_size: int = 10


class ToolCallChecker:
    def __init__(self, config: ToolCallCheckerConfig) -> None:
        self._config = config
        self._strike_counter = OccurrencesCounter(comparator=_is_same_tool_call, n=config.max_strike_length + 1)
        self._occurrences_counter = OccurrencesCounter(
            comparator=_is_same_tool_call, n=max(config.max_total_occurrences + 1, config.window_size)
        )
        self.cycle_found = False
        self.enabled = True

    def register(self, value: MessageToolCallContent) -> None:
        if not self.enabled:
            return

        strike_length = self._strike_counter.update(value)
        if strike_length > self._config.max_strike_length:
            self.cycle_found = True

        occurrences = self._occurrences_counter.update(value)
        if occurrences > self._config.max_total_occurrences:
            self.cycle_found = True

    def reset(self, current: MessageToolCallContent | None = None) -> None:
        self._strike_counter.reset(current)
        self._occurrences_counter.reset(current)
        self.cycle_found = False

    @property
    def config(self) -> ToolCallCheckerConfig:
        return self._config


def _is_same_tool_call(a: MessageToolCallContent | None, b: MessageToolCallContent | None) -> bool:
    return bool(a and b and a.tool_name == b.tool_name and a.args == b.args and a.type == b.type)
