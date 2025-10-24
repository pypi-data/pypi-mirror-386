# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from pydantic import BaseModel

from beeai_framework.adapters.watsonx_orchestrate.serve.agent import (
    WatsonxOrchestrateServerAgent,
    WatsonxOrchestrateServerAgentEmitFn,
    WatsonxOrchestrateServerAgentMessageEvent,
    WatsonxOrchestrateServerAgentThinkEvent,
    WatsonxOrchestrateServerAgentToolCallEvent,
    WatsonxOrchestrateServerAgentToolResponse,
)
from beeai_framework.agents.requirement import RequirementAgent
from beeai_framework.agents.requirement.utils._tool import FinalAnswerTool, FinalAnswerToolSchema
from beeai_framework.backend import AnyMessage
from beeai_framework.emitter import EmitterOptions, EventMeta
from beeai_framework.tools import Tool, ToolStartEvent, ToolSuccessEvent
from beeai_framework.tools.think import ThinkSchema, ThinkTool
from beeai_framework.utils.cloneable import Cloneable


class WatsonxOrchestrateServerRequirementAgent(WatsonxOrchestrateServerAgent[RequirementAgent]):
    @property
    def model_id(self) -> str:
        return self._agent._llm.model_id

    async def _stream(self, input: list[AnyMessage], emit: WatsonxOrchestrateServerAgentEmitFn) -> None:
        cloned_agent = await self._agent.clone() if isinstance(self._agent, Cloneable) else self._agent

        async def on_tool_success(data: ToolSuccessEvent, meta: EventMeta) -> None:
            assert meta.trace, "ToolSuccessEvent must have trace"
            assert isinstance(meta.creator, Tool)

            if isinstance(meta.creator, FinalAnswerTool):
                await emit(
                    WatsonxOrchestrateServerAgentMessageEvent(
                        text=data.input.response
                        if isinstance(data.input, FinalAnswerToolSchema)
                        else data.input.model_dump_json(indent=2),
                    )
                )
            else:
                await emit(
                    WatsonxOrchestrateServerAgentToolResponse(
                        name=meta.creator.name, id=meta.trace.run_id, result=data.output.get_text_content()
                    )
                )

        async def on_tool_start(data: ToolStartEvent, meta: EventMeta) -> None:
            assert meta.trace, "ToolStartEvent must have trace"
            assert isinstance(meta.creator, Tool)

            if isinstance(meta.creator, FinalAnswerTool):
                return

            await emit(
                WatsonxOrchestrateServerAgentToolCallEvent(
                    id=meta.trace.run_id,
                    name=meta.creator.name,
                    args=data.input.model_dump() if isinstance(data.input, BaseModel) else data.input,
                )
            )
            if isinstance(meta.creator, ThinkTool):
                assert isinstance(data.input, ThinkSchema), "ThinkTool must use ThinkSchema as an input"
                await emit(
                    WatsonxOrchestrateServerAgentThinkEvent(
                        text=f"{data.input.thoughts}\n\nNext Steps:\n"
                        + (
                            "\n- ".join(data.input.next_step)
                            if isinstance(data.input, ThinkSchema)
                            else data.input.model_dump_json(indent=2)
                        ),
                    )
                )

        await (
            cloned_agent.run(input)
            .on(
                lambda event: isinstance(event.creator, Tool) and event.name == "start",
                on_tool_start,
                EmitterOptions(match_nested=True),
            )
            .on(
                lambda event: isinstance(event.creator, Tool) and event.name == "success",
                on_tool_success,
                EmitterOptions(match_nested=True),
            )
        )
