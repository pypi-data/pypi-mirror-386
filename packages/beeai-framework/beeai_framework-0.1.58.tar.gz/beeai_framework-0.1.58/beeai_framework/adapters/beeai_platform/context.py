# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import contextlib
from collections.abc import Callable
from contextvars import ContextVar
from typing import Any, Self

from beeai_framework.adapters.beeai_platform.backend.chat import BeeAIPlatformChatModel
from beeai_framework.adapters.beeai_platform.serve.types import BaseBeeAIPlatformExtensions
from beeai_framework.logger import Logger
from beeai_framework.utils.io import setup_io_context

try:
    from beeai_sdk.a2a.extensions import (
        FormRender,
        LLMServiceExtensionServer,
        TextField,
    )
    from beeai_sdk.server.context import RunContext
except ModuleNotFoundError as e:
    raise ModuleNotFoundError(
        "Optional module [beeai-platform] not found.\nRun 'pip install \"beeai-framework[beeai-platform]\"' to install."
    ) from e

logger = Logger(__name__)


_storage: ContextVar["BeeAIPlatformContext"] = ContextVar("beeai_platform")


class BeeAIPlatformContext:
    def __init__(
        self,
        context: RunContext,
        *,
        llm: LLMServiceExtensionServer | None = None,
        extra_extensions: BaseBeeAIPlatformExtensions,
    ) -> None:
        self.context = context
        self._llm = llm
        self._cleanup: list[Callable[[], None]] = []
        self._extensions = extra_extensions

    @property
    def extensions(self) -> BaseBeeAIPlatformExtensions:
        return self._extensions

    @staticmethod
    def get() -> "BeeAIPlatformContext":
        return _storage.get()

    def __enter__(self) -> Self:
        ctx_key = _storage.set(self)
        self._cleanup.append(lambda: _storage.reset(ctx_key))
        self._cleanup.append(setup_io_context(read=self._read))
        if self._llm is not None:
            self._cleanup.append(BeeAIPlatformChatModel.set_context(self._llm))
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        while self._cleanup:
            cleanup = self._cleanup.pop(0)
            with contextlib.suppress(Exception):
                cleanup()

    async def _read(self, prompt: str) -> str:
        try:
            answer_field_id = "answer"
            form_data = await self._extensions["form"].request_form(
                form=FormRender(
                    id="form",
                    title=prompt,
                    description="",
                    columns=1,
                    submit_label="Send",
                    fields=[
                        TextField(
                            id=answer_field_id,
                            label="Answer",
                            required=True,
                            placeholder="",
                            type="text",
                            default_value="",
                            col_span=1,
                        )
                    ],
                )
            )
            return str(form_data.values[answer_field_id].value)
        except ValueError as e:
            logger.warning(f"Failed to process form: {e}")
            return ""
