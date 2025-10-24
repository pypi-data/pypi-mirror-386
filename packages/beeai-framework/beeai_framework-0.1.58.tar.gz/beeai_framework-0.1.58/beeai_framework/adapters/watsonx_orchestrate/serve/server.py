# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import contextlib
from collections.abc import Sequence
from typing import Any, Self

import uvicorn
from pydantic import BaseModel
from typing_extensions import TypedDict, TypeVar, override

import beeai_framework.adapters.watsonx_orchestrate.serve._factories as factories
from beeai_framework.adapters.watsonx_orchestrate.serve.agent import WatsonxOrchestrateServerAgent
from beeai_framework.adapters.watsonx_orchestrate.serve.api import WatsonxOrchestrateAPI
from beeai_framework.agents.react import ReActAgent
from beeai_framework.agents.requirement import RequirementAgent
from beeai_framework.agents.tool_calling import ToolCallingAgent
from beeai_framework.logger import Logger
from beeai_framework.runnable import Runnable
from beeai_framework.serve import MemoryManager
from beeai_framework.serve.errors import FactoryAlreadyRegisteredError
from beeai_framework.serve.server import Server
from beeai_framework.utils import ModelLike
from beeai_framework.utils.models import to_model

AnyAgentLike = TypeVar("AnyAgentLike", bound=Runnable[Any], default=Runnable[Any])
AnyWatsonxOrchestrateServerAgentLike = TypeVar(
    "AnyWatsonxOrchestrateServerAgentLike",
    bound=WatsonxOrchestrateServerAgent[Any],
    default=WatsonxOrchestrateServerAgent[Any],
)

logger = Logger(__name__)


class WatsonxOrchestrateServerConfig(BaseModel):
    """Configuration for the WatsonxOrchestrateServer."""

    host: str = "0.0.0.0"
    port: int = 9999
    api_key: str | None = None

    fast_api_kwargs: dict[str, Any] | None = None


class WatsonxOrchestrateServerMetadata(TypedDict, total=False):
    pass


class WatsonxOrchestrateServer(
    Server[
        AnyAgentLike,
        AnyWatsonxOrchestrateServerAgentLike,
        WatsonxOrchestrateServerConfig,
    ],
):
    def __init__(
        self,
        *,
        config: ModelLike[WatsonxOrchestrateServerConfig] | None = None,
        api_cls: type[WatsonxOrchestrateAPI] = WatsonxOrchestrateAPI,
        memory_manager: MemoryManager | None = None,
    ) -> None:
        super().__init__(
            config=to_model(WatsonxOrchestrateServerConfig, config or WatsonxOrchestrateServerConfig()),
            memory_manager=memory_manager,
        )
        self._api_cls = api_cls

    def serve(self) -> None:
        if not self._members:
            raise ValueError("No agents registered to the server.")

        member = self._members[0]
        factory = type(self)._factories[type(member)]

        api = self._api_cls(
            create_agent=lambda: factory(member),
            api_key=self._config.api_key,
            fast_api_kwargs=self._config.fast_api_kwargs,
            memory_manager=self._memory_manager,
        )
        uvicorn.run(api.app, host=self._config.host, port=self._config.port)

    @override
    def register(self, input: AnyAgentLike) -> Self:
        if self._members:
            raise ValueError("WatsonxOrchestrateServer only supports one agent.")

        return super().register(input)

    @override
    def register_many(self, input: Sequence[AnyAgentLike]) -> Self:
        raise NotImplementedError("register_many is not implemented for WatsonxOrchestrateServer")


with contextlib.suppress(FactoryAlreadyRegisteredError):
    WatsonxOrchestrateServer.register_factory(
        ReActAgent, lambda agent: factories.WatsonxOrchestrateServerReActAgent(agent)
    )

with contextlib.suppress(FactoryAlreadyRegisteredError):
    WatsonxOrchestrateServer.register_factory(
        ToolCallingAgent, lambda agent: factories.WatsonxOrchestrateServerToolCallingAgent(agent)
    )

with contextlib.suppress(FactoryAlreadyRegisteredError):
    WatsonxOrchestrateServer.register_factory(
        RequirementAgent, lambda agent: factories.WatsonxOrchestrateServerRequirementAgent(agent)
    )

with contextlib.suppress(FactoryAlreadyRegisteredError):
    WatsonxOrchestrateServer.register_factory(Runnable, lambda agent: factories.WatsonxOrchestrateServerRunnable(agent))  # type: ignore[type-abstract]
