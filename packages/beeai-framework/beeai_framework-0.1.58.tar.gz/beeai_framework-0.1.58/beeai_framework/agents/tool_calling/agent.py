# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import json
from collections.abc import Sequence
from typing import Any, Unpack

from pydantic import BaseModel, Field, create_model

from beeai_framework.agents import AgentError, AgentOptions, BaseAgent
from beeai_framework.agents.tool_calling.events import (
    ToolCallingAgentStartEvent,
    ToolCallingAgentSuccessEvent,
    tool_calling_agent_event_types,
)
from beeai_framework.agents.tool_calling.prompts import (
    ToolCallingAgentCycleDetectionPromptInput,
    ToolCallingAgentTaskPromptInput,
)
from beeai_framework.agents.tool_calling.types import (
    ToolCallingAgentOutput,
    ToolCallingAgentRunState,
    ToolCallingAgentTemplateFactory,
    ToolCallingAgentTemplates,
    ToolCallingAgentTemplatesKeys,
)
from beeai_framework.agents.tool_calling.utils import ToolCallChecker, ToolCallCheckerConfig
from beeai_framework.agents.types import AgentExecutionConfig, AgentMeta
from beeai_framework.backend import AnyMessage
from beeai_framework.backend.chat import ChatModel
from beeai_framework.backend.message import (
    AssistantMessage,
    MessageToolCallContent,
    MessageToolResultContent,
    SystemMessage,
    ToolMessage,
    UserMessage,
)
from beeai_framework.backend.utils import parse_broken_json
from beeai_framework.context import RunContext
from beeai_framework.emitter import Emitter
from beeai_framework.memory.base_memory import BaseMemory
from beeai_framework.memory.unconstrained_memory import UnconstrainedMemory
from beeai_framework.runnable import runnable_entry
from beeai_framework.template import PromptTemplate
from beeai_framework.tools.errors import ToolError
from beeai_framework.tools.tool import AnyTool
from beeai_framework.tools.tool import tool as create_tool
from beeai_framework.tools.types import StringToolOutput
from beeai_framework.utils.counter import RetryCounter
from beeai_framework.utils.models import update_model
from beeai_framework.utils.strings import find_first_pair, generate_random_string, to_json


class ToolCallingAgent(BaseAgent[ToolCallingAgentOutput]):
    def __init__(
        self,
        *,
        llm: ChatModel,
        memory: BaseMemory | None = None,
        tools: Sequence[AnyTool] | None = None,
        templates: dict[ToolCallingAgentTemplatesKeys, PromptTemplate[Any] | ToolCallingAgentTemplateFactory]
        | None = None,
        save_intermediate_steps: bool = True,
        meta: AgentMeta | None = None,
        tool_call_checker: ToolCallCheckerConfig | bool = True,
        final_answer_as_tool: bool = True,
    ) -> None:
        super().__init__()
        self._llm = llm
        self._memory = memory or UnconstrainedMemory()
        self._tools = tools or []
        self._templates = self._generate_templates(templates)
        self._save_intermediate_steps = save_intermediate_steps
        self._meta = meta
        self._tool_call_checker = tool_call_checker
        self._final_answer_as_tool = final_answer_as_tool

    @runnable_entry
    async def run(self, input: str | list[AnyMessage], /, **kwargs: Unpack[AgentOptions]) -> ToolCallingAgentOutput:
        """Execute the agent.

        Args:
            input: The input to the agent (if list of messages, uses the last message as input)
            expected_output: Pydantic model or instruction for steering the agent towards an expected output format.
            total_max_retries: Maximum number of model retries.
            max_retries_per_step: Maximum number of model retries per step.
            max_iterations: Maximum number of iterations.
            backstory: Additional piece of information or background for the agent.
            signal: The agent abort signal
            context: A dictionary that can be used to pass additional context to the agent

        Returns:
            The agent output.
        """
        if not input and self._memory.is_empty():
            raise ValueError(
                "Invalid input. The input must be a non-empty string or list of messages when memory is empty."
            )

        run_config = AgentExecutionConfig(
            max_retries_per_step=kwargs.get("max_retries_per_step", 3),
            total_max_retries=kwargs.get("total_max_retries", 20),
            max_iterations=kwargs.get("max_iterations", 10),
        )
        expected_output = kwargs.get("expected_output")

        run_context = RunContext.get()
        state = ToolCallingAgentRunState(memory=UnconstrainedMemory(), result=None, iteration=0)
        await state.memory.add(SystemMessage(self._templates.system.render()))
        await state.memory.add_many(self.memory.messages)

        if isinstance(input, list):
            await state.memory.add_many(input)

        user_message: UserMessage | None = None
        if isinstance(input, str) and input:
            task_input = ToolCallingAgentTaskPromptInput(
                prompt=input,
                context=kwargs.get("backstory"),
                expected_output=expected_output if isinstance(expected_output, str) else None,
            )
            user_message = UserMessage(self._templates.task.render(task_input))
            await state.memory.add(user_message)

        global_retries_counter = RetryCounter(error_type=AgentError, max_retries=run_config.total_max_retries or 1)

        final_answer_schema_cls: type[BaseModel] = (
            expected_output
            if (
                expected_output is not None
                and isinstance(expected_output, type)
                and issubclass(expected_output, BaseModel)
            )
            else create_model(
                "FinalAnswer",
                response=(
                    str,
                    Field(description=expected_output or None),
                ),
            )
        )

        @create_tool(
            name="final_answer",
            description="Sends the final answer to the user",
            input_schema=final_answer_schema_cls,
        )
        def final_answer_tool(**kwargs: Any) -> StringToolOutput:
            if final_answer_schema_cls is expected_output:
                dump = final_answer_schema_cls.model_validate(kwargs)
                state.result = AssistantMessage(to_json(dump.model_dump()))
            else:
                state.result = AssistantMessage(kwargs["response"])

            return StringToolOutput("Message has been sent")

        tools = [*self._tools, final_answer_tool]
        tool_call_checker = self._create_tool_call_checker()
        final_answer_as_tool = self._final_answer_as_tool

        while state.result is None:
            state.iteration += 1

            if run_config.max_iterations and state.iteration > run_config.max_iterations:
                raise AgentError(f"Agent was not able to resolve the task in {state.iteration} iterations.")

            await run_context.emitter.emit(
                "start",
                ToolCallingAgentStartEvent(state=state),
            )
            response = await self._llm.run(
                state.memory.messages,
                tools=tools,
                tool_choice=("required" if len(tools) > 1 else tools[0]) if final_answer_as_tool else "auto",
            )

            text_messages = response.get_text_messages()
            tool_call_messages = response.get_tool_calls()

            if not final_answer_as_tool and not tool_call_messages and text_messages:
                full_text = "".join(msg.text for msg in text_messages)
                json_object_pair = find_first_pair(full_text, ("{", "}"))
                final_answer_input = parse_broken_json(json_object_pair.outer) if json_object_pair else None
                if not final_answer_input and final_answer_schema_cls is not expected_output:
                    final_answer_input = {"response": full_text}

                if not final_answer_input:
                    tools = [final_answer_tool]
                    final_answer_as_tool = True
                    continue

                tool_call_message = MessageToolCallContent(
                    type="tool-call",
                    id=f"call_{generate_random_string(8).lower()}",
                    tool_name=final_answer_tool.name,
                    args=to_json(final_answer_input),
                )
                tool_call_messages.append(tool_call_message)
                await state.memory.add(AssistantMessage(tool_call_message))
            else:
                await state.memory.add_many(response.output)

            for tool_call in tool_call_messages:
                try:
                    tool = next((tool for tool in tools if tool.name == tool_call.tool_name), None)
                    if not tool:
                        raise ToolError(f"Tool '{tool_call.tool_name}' does not exist!")

                    tool_call_checker.register(tool_call)
                    if tool_call_checker.cycle_found:
                        await state.memory.delete_many(response.output)
                        await state.memory.add(
                            UserMessage(
                                self._templates.cycle_detection.render(
                                    ToolCallingAgentCycleDetectionPromptInput(
                                        tool_args=tool_call.args,
                                        tool_name=tool_call.tool_name,
                                        final_answer_tool=final_answer_tool.name,
                                    )
                                ),
                            ),
                        )
                        tool_call_checker.reset(tool_call)
                        break

                    tool_input = json.loads(tool_call.args)
                    tool_response = await tool.run(tool_input).context(
                        {"state": state.model_dump(), "tool_call_msg": tool_call}
                    )
                    await state.memory.add(
                        ToolMessage(
                            MessageToolResultContent(
                                result=tool_response.get_text_content(),
                                tool_name=tool_call.tool_name,
                                tool_call_id=tool_call.id,
                            )
                        )
                    )
                except ToolError as e:
                    global_retries_counter.use(e)
                    await state.memory.add(
                        ToolMessage(
                            MessageToolResultContent(
                                result=self._templates.tool_error.render({"reason": e.explain()}),
                                tool_name=tool_call.tool_name,
                                tool_call_id=tool_call.id,
                            )
                        )
                    )

            # handle empty messages for some models
            if not tool_call_messages and not text_messages:
                await state.memory.add(AssistantMessage("\n", {"tempMessage": True}))
            else:
                await state.memory.delete_many(
                    [msg for msg in state.memory.messages if msg.meta.get("tempMessage", False)]
                )

            await run_context.emitter.emit(
                "success",
                ToolCallingAgentSuccessEvent(state=state),
            )

        assert state.result is not None
        if self._save_intermediate_steps:
            self.memory.reset()
            await self.memory.add_many(state.memory.messages[1:])
        else:
            if user_message is not None:
                await self.memory.add(user_message)
            await self.memory.add_many(state.memory.messages[-2:])

        return ToolCallingAgentOutput(output=[state.result], output_structured=state.result, state=state)

    def _create_emitter(self) -> Emitter:
        return Emitter.root().child(
            namespace=["agent", "tool_calling"], creator=self, events=tool_calling_agent_event_types
        )

    @property
    def meta(self) -> AgentMeta:
        return self._meta or super().meta

    @property
    def memory(self) -> BaseMemory:
        return self._memory

    @memory.setter
    def memory(self, memory: BaseMemory) -> None:
        self._memory = memory

    @staticmethod
    def _generate_templates(
        overrides: dict[ToolCallingAgentTemplatesKeys, PromptTemplate[Any] | ToolCallingAgentTemplateFactory]
        | None = None,
    ) -> ToolCallingAgentTemplates:
        templates = ToolCallingAgentTemplates()
        if overrides is None:
            return templates

        for name, _info in ToolCallingAgentTemplates.model_fields.items():
            override: PromptTemplate[Any] | ToolCallingAgentTemplateFactory | None = overrides.get(name)
            if override is None:
                continue
            elif isinstance(override, PromptTemplate):
                setattr(templates, name, override)
            else:
                setattr(templates, name, override(getattr(templates, name)))
        return templates

    async def clone(self) -> "ToolCallingAgent":
        cloned = ToolCallingAgent(
            llm=await self._llm.clone(),
            memory=await self._memory.clone(),
            tools=[await tool.clone() for tool in self._tools],
            templates=self._templates.model_dump(),
            tool_call_checker=self._tool_call_checker,
            save_intermediate_steps=self._save_intermediate_steps,
            meta=self._meta,
            final_answer_as_tool=self._final_answer_as_tool,
        )
        cloned.emitter = await self.emitter.clone()
        return cloned

    def _create_tool_call_checker(self) -> ToolCallChecker:
        config = ToolCallCheckerConfig()
        update_model(config, sources=[self._tool_call_checker])

        instance = ToolCallChecker(config)
        instance.enabled = self._tool_call_checker is not False
        return instance
