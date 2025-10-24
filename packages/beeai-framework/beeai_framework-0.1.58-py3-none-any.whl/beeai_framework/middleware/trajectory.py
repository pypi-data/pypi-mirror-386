# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import sys
from collections.abc import Callable
from typing import Any, Protocol, runtime_checkable

from beeai_framework.agents import BaseAgent
from beeai_framework.agents.requirement.requirements import Requirement
from beeai_framework.backend import AnyMessage, ChatModel
from beeai_framework.context import RunContext, RunContextFinishEvent, RunContextStartEvent, RunMiddlewareProtocol
from beeai_framework.emitter import Emitter, EmitterOptions, EventMeta
from beeai_framework.logger import Logger
from beeai_framework.tools import Tool
from beeai_framework.utils.strings import to_json


@runtime_checkable
class Writeable(Protocol):
    def write(self, s: str) -> int: ...


def logger_to_writeable(logger: Logger) -> Writeable:
    class CustomWriteable(Writeable):
        def write(self, s: str) -> int:
            msg = s.removesuffix("\n")
            logger.log(msg=msg, level=logger.level)
            return len(msg)

    return CustomWriteable()


class GlobalTrajectoryMiddleware(RunMiddlewareProtocol):
    def __init__(
        self,
        *,
        target: Writeable | Logger | None = None,
        included: list[type] | None = None,
        excluded: list[type] | None = None,
        pretty: bool = False,
        prefix_by_type: dict[type, str] | None = None,
        exclude_none: bool = True,
        enabled: bool = True,
        match_nested: bool = True,
    ) -> None:
        """
        Args:
            target: Specify a file or stream to write the trajectory to.
            included: List of classes to include in the trajectory.
            excluded: List of classes to exclude from the trajectory.
            pretty: Use pretty formatting for the trajectory.
            prefix_by_type: Customize how instances of individual classes should be printed.
            exclude_none: Exclude None values from the printing.
            enabled: Enable/Disable the logging.
            match_nested: Whether to observe trajectories of nested run contexts.
        """
        super().__init__()
        self.enabled = enabled
        self._included = included or []
        self._excluded = excluded or []
        self._cleanups: list[Callable[[], None]] = []
        self._target: Writeable = (
            logger_to_writeable(target) if isinstance(target, Logger) else target if target is not None else sys.stdout
        )
        self._ctx: RunContext | None = None
        self._pretty = pretty
        self._last_message: AnyMessage | None = None
        self._trace_level: dict[str, int] = {}
        self._prefix_by_type = {BaseAgent: "🤖 ", ChatModel: "💬 ", Tool: "🛠️ ", Requirement: "🔎 "} | (
            prefix_by_type or {}
        )
        self._exclude_none = exclude_none
        self._match_nested = match_nested

    def _bind_nested_emitter(self, emitter: Emitter) -> None:
        def matcher(meta: EventMeta) -> bool:
            return (
                meta.name == "start"
                and bool(meta.context.get("internal"))
                and isinstance(meta.creator, RunContext)
                and meta.creator.emitter is not emitter
            )

        def handler(data: Any, meta: EventMeta) -> None:
            assert isinstance(meta.creator, RunContext)
            self._bind_emitter(meta.creator.emitter)
            self.on_internal_start(data, meta)

        self._cleanups.append(
            emitter.on(
                matcher,
                handler,
                EmitterOptions(match_nested=True, is_blocking=True),
            )
        )

    def _bind_emitter(self, emitter: Emitter) -> None:
        # must be last to be executed as first
        self._cleanups.append(
            emitter.on("*.*", lambda _, event: self._log_trace_id(event), EmitterOptions(match_nested=True))
        )

        def bind_internal_event(name: str) -> None:
            self._cleanups.append(
                emitter.match(
                    lambda event: event.name == name
                    and bool(event.context.get("internal"))
                    and isinstance(event.creator, RunContext),
                    getattr(self, f"on_internal_{name}"),
                    EmitterOptions(match_nested=False),
                )
            )

        for name in ["start", "finish"]:
            bind_internal_event(name)

        if self._match_nested:
            self._bind_nested_emitter(emitter)

    def bind(self, ctx: RunContext) -> None:
        while self._cleanups:
            self._cleanups.pop(0)()

        self._trace_level.clear()
        self._trace_level[ctx.run_id] = 0
        self._ctx = ctx

        self._bind_emitter(ctx.emitter)

    def _log_trace_id(self, meta: EventMeta) -> None:
        if not meta.trace or not meta.trace.run_id:
            return

        if meta.trace.run_id in self._trace_level:
            return

        if meta.trace.parent_run_id:
            parent_level = self._trace_level.get(meta.trace.parent_run_id, 0)
            self._trace_level[meta.trace.run_id] = parent_level + 1

    def _is_allowed(self, meta: EventMeta) -> bool:
        target: object = meta.creator
        if isinstance(target, RunContext):
            target = target.instance

        for excluded in self._excluded:
            if isinstance(target, excluded):
                return False

        if not self._included:
            return True

        return any(isinstance(target, included) for included in self._included)

    def _extract_name(self, meta: EventMeta) -> str:
        target: object = meta.creator
        if isinstance(target, RunContext):
            target = target.instance

        class_name = type(target).__name__

        prefix = next((v for k, v in self._prefix_by_type.items() if isinstance(target, k)), "")

        if isinstance(target, BaseAgent):
            return f"{prefix}{class_name}[{target.meta.name}][{meta.name}]"
        elif isinstance(target, Tool | Requirement):
            return f"{prefix}{class_name}[{target.name}][{meta.name}]"

        return f"{prefix}{class_name}[{meta.name}]"

    def _get_trace_level(self, meta: EventMeta) -> tuple[int, int]:
        assert meta.trace
        indent = self._trace_level[meta.trace.run_id]
        parent_indent = self._trace_level.get(meta.trace.parent_run_id, 0)  # type: ignore
        return indent, parent_indent

    def _write(self, text: str, meta: EventMeta) -> None:
        assert meta.trace

        self._log_trace_id(meta)
        if not self._is_allowed(meta):
            return

        if not self.enabled:
            return

        indent, indent_parent = self._get_trace_level(meta)
        indent_diff = indent - indent_parent

        prefix = ""
        prefix += "  " * indent_parent
        if indent_parent > 0:
            prefix += "  " * indent_parent

        if meta.name == "finish" and indent:
            prefix += "<"

        prefix += "--" * indent_diff

        if meta.name == "start" and prefix and indent:
            prefix += ">"

        if prefix:
            prefix = f"{prefix} "

        name = self._extract_name(meta)
        self._target.write(f"{prefix}{name}: {text}\n")

    def _format_data(self, value: Any) -> str:
        if isinstance(value, str | int | bool | float | None):
            return str(value)

        return to_json(value, indent=2 if self._pretty else None, sort_keys=False, exclude_none=self._exclude_none)

    def on_internal_start(self, data: RunContextStartEvent, meta: EventMeta) -> None:
        self._write(self._format_data(data), meta)

    def on_internal_finish(self, data: RunContextFinishEvent, meta: EventMeta) -> None:
        if data.error is None:
            self._write(self._format_data(data.output), meta)
        else:
            self._write("error has occurred", meta)
            self._write(data.error.explain(), meta)
