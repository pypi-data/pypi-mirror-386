# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
import uuid
from collections.abc import Sequence
from typing import Any

from typing_extensions import Unpack

from beeai_framework.agents import AgentError, AgentExecutionConfig, AgentMeta, AgentOptions, BaseAgent
from beeai_framework.agents.requirement.events import (
    RequirementAgentFinalAnswerEvent,
    RequirementAgentStartEvent,
    RequirementAgentSuccessEvent,
    requirement_agent_event_types,
)
from beeai_framework.agents.requirement.prompts import (
    RequirementAgentTaskPromptInput,
    RequirementAgentToolErrorPromptInput,
)
from beeai_framework.agents.requirement.requirements.requirement import Requirement, Rule
from beeai_framework.agents.requirement.types import (
    RequirementAgentOutput,
    RequirementAgentRequest,
    RequirementAgentRunState,
    RequirementAgentRunStateStep,
    RequirementAgentTemplateFactory,
    RequirementAgentTemplates,
    RequirementAgentTemplatesKeys,
)
from beeai_framework.agents.requirement.utils._llm import RequirementsReasoner, _create_system_message
from beeai_framework.agents.requirement.utils._tool import FinalAnswerTool, _run_tools
from beeai_framework.agents.tool_calling.utils import ToolCallChecker, ToolCallCheckerConfig
from beeai_framework.backend import AnyMessage
from beeai_framework.backend.chat import ChatModel
from beeai_framework.backend.message import (
    AssistantMessage,
    MessageTextContent,
    MessageToolCallContent,
    MessageToolResultContent,
    ToolMessage,
    UserMessage,
)
from beeai_framework.backend.utils import parse_broken_json
from beeai_framework.context import RunContext, RunMiddlewareType
from beeai_framework.emitter import Emitter, EventMeta
from beeai_framework.memory.base_memory import BaseMemory
from beeai_framework.memory.unconstrained_memory import UnconstrainedMemory
from beeai_framework.memory.utils import extract_last_tool_call_pair
from beeai_framework.middleware.stream_tool_call import StreamToolCallMiddleware, StreamToolCallMiddlewareUpdateEvent
from beeai_framework.runnable import runnable_entry
from beeai_framework.template import PromptTemplate
from beeai_framework.tools import AnyTool
from beeai_framework.utils.counter import RetryCounter
from beeai_framework.utils.dicts import exclude_none
from beeai_framework.utils.lists import cast_list
from beeai_framework.utils.models import update_model
from beeai_framework.utils.strings import find_first_pair, generate_random_string, to_json

RequirementAgentRequirement = Requirement[RequirementAgentRunState]


class RequirementAgent(BaseAgent[RequirementAgentOutput]):
    """
    The RequirementAgent is a declarative AI agent implementation that provides predictable,
    controlled execution behavior across different language models through rule-based constraints.
    Language models vary significantly in their reasoning capabilities and tool-calling sophistication, but
    RequirementAgent normalizes these differences by enforcing consistent execution patterns
    regardless of the underlying model's strengths or weaknesses.
    Rules can be configured as strict or flexible as necessary, adapting to task requirements while ensuring consistent
    execution regardless of the underlying model's reasoning or tool-calling capabilities.
    """

    def __init__(
        self,
        *,
        llm: ChatModel | str,
        memory: BaseMemory | None = None,
        tools: Sequence[AnyTool] | None = None,
        requirements: Sequence[RequirementAgentRequirement] | None = None,
        name: str | None = None,
        description: str | None = None,
        role: str | None = None,
        instructions: str | list[str] | None = None,
        notes: str | list[str] | None = None,
        tool_call_checker: ToolCallCheckerConfig | bool = True,
        final_answer_as_tool: bool = True,
        save_intermediate_steps: bool = True,
        templates: dict[RequirementAgentTemplatesKeys, PromptTemplate[Any] | RequirementAgentTemplateFactory]
        | RequirementAgentTemplates
        | None = None,
        middlewares: list[RunMiddlewareType] | None = None,
    ) -> None:
        """
        Initializes an instance of the RequirementAgent class.

        Args:
            llm:
                The language model to be used for chat functionality. Can be provided as
                an instance of ChatModel or as a string representing the model name.

            tools:
                A sequence of tools that the agent can use during the execution. Default is an empty list.

            requirements:
                A sequence of requirements that constrain the agent's behavior.

            memory:
                The memory instance to store conversation history or state. If none is
                provided, a default UnconstrainedMemory instance will be used.

            name:
                A name of the agent which should emphasize its purpose.
                This property is used in multi-agent components like HandoffTool or when exposing the agent as a server.

            description:
                A brief description of the agent abilities.
                This property is used in multi-agent components like HandoffTool or when exposing the agent as a server.

            role:
                Role for the agent. Will be part of the system prompt.

            instructions:
                Instructions for the agents. Will be part of the system prompt. Can be a single string or a list of
                strings. If a list is provided, it will be formatted as a single newline-separated string.

            save_intermediate_steps:
                Determines whether intermediate steps during execution should be preserved between individual turns.
                If enabled (default), the agent can reuse existing tool results and might provide a better result
                  but consumes more tokens.

            middlewares:
                A list of middlewares to be applied for an upcoming execution.
                Useful for logging and altering the behavior.

            templates:
                Templates define prompts that the model will work with. Use to fully customize the prompts.

            final_answer_as_tool:
                Whether the final output is communicated as a tool call (default is True).
                Disable when your outputs are truncated or low-quality.

            tool_call_checker:
                Configuration for a component that detects a situation when LLM generates tool calls in a cycle.

            notes:
                Additional notes for the agents. The only difference from `instructions` is that notes are at the very
                end of the system prompt and should be more related to the output and its formatting.
        """
        super().__init__(middlewares=middlewares)
        self._llm = ChatModel.from_name(llm) if isinstance(llm, str) else llm
        self._memory = memory or UnconstrainedMemory()
        self._templates = self._generate_templates(templates)
        self._save_intermediate_steps = save_intermediate_steps
        self._tool_call_checker = tool_call_checker
        self._final_answer_as_tool = final_answer_as_tool
        if role or instructions or notes:
            self._templates.system.update(
                defaults=exclude_none(
                    {
                        "role": role,
                        "instructions": "\n -".join(cast_list(instructions)) if instructions else None,
                        "notes": "\n -".join(cast_list(notes)) if notes else None,
                    }
                )
            )
        self._tools = list(tools or [])
        self._requirements = list(requirements or [])
        self._meta = AgentMeta(name=name or "", description=description or "", tools=self._tools)

    @runnable_entry
    async def run(self, input: str | list[AnyMessage], /, **kwargs: Unpack[AgentOptions]) -> RequirementAgentOutput:
        """Execute the agent.

        Args:
            input: The input to the agent (if list of messages, uses the last message as input)
            expected_output: Pydantic model or instruction for steering the agent towards an expected output format.
            total_max_retries: Maximum number of model retries.
            max_retries_per_step: Maximum number of model retries per step.
            max_iterations: Maximum number of iterations.
            backstory: Additional piece of information or background for the agent.
            signal: The abort signal
            context: A dictionary that can be used to pass additional context to the agent

        Returns:
            The agent output.
        """
        run_config = AgentExecutionConfig(
            max_retries_per_step=kwargs.get("max_retries_per_step", 3),
            total_max_retries=kwargs.get("total_max_retries", 20),
            max_iterations=kwargs.get("max_iterations", 20),
        )
        expected_output = kwargs.get("expected_output")

        async def init_state() -> tuple[RequirementAgentRunState, UserMessage | None]:
            state = RequirementAgentRunState(
                memory=UnconstrainedMemory(), steps=[], iteration=0, answer=None, result=None
            )
            await state.memory.add_many(self.memory.messages)

            if not input:
                return state, None

            *msgs, last_message = [UserMessage(input)] if isinstance(input, str) else input
            await state.memory.add_many(msgs)
            if isinstance(last_message, UserMessage) and last_message.text:
                user_message = UserMessage(
                    self._templates.task.render(
                        RequirementAgentTaskPromptInput(
                            prompt=last_message.text,
                            context=kwargs.get("backstory"),
                            expected_output=expected_output
                            if isinstance(expected_output, str)
                            else None,  # TODO: validate
                        )
                    ),
                    meta=last_message.meta.copy(),
                )
                user_message.content.extend(
                    [content for content in last_message.content if not isinstance(content, MessageTextContent)]
                )
                await state.memory.add(user_message)
            else:
                await state.memory.add(last_message)
                user_message = None

            return state, user_message

        state, user_message = await init_state()
        run_context = RunContext.get()

        reasoner = RequirementsReasoner(
            tools=self._tools,
            final_answer=FinalAnswerTool(expected_output, state=state),
            context=run_context,
        )
        await reasoner.update(self._requirements)

        tool_call_cycle_checker = self._create_tool_call_checker()
        tool_call_retry_counter = RetryCounter(error_type=AgentError, max_retries=run_config.total_max_retries or 1)
        force_final_answer_as_tool = self._final_answer_as_tool
        tmp_rules: list[Rule] = []

        while state.answer is None:
            state.iteration += 1

            if run_config.max_iterations and state.iteration > run_config.max_iterations:
                raise AgentError(f"Agent was not able to resolve the task in {state.iteration} iterations.")

            request = await reasoner.create_request(
                state, force_tool_call=force_final_answer_as_tool, extra_rules=tmp_rules
            )
            tmp_rules.clear()

            await run_context.emitter.emit(
                "start",
                RequirementAgentStartEvent(state=state, request=request),
            )

            stream_middleware = self._stream_final_answer(request, run_context, state)
            response = await self._llm.run(
                [
                    _create_system_message(
                        template=self._templates.system,
                        request=request,
                    ),
                    *state.memory.messages,
                ],
                max_retries=run_config.max_retries_per_step,
                tools=request.allowed_tools,
                tool_choice=request.tool_choice,
                stream_partial_tool_calls=True,
            ).middleware(stream_middleware)
            stream_middleware.unbind()

            await state.memory.add_many(response.output)

            text_messages = response.get_text_messages()
            tool_call_messages = response.get_tool_calls()

            if not tool_call_messages and text_messages and request.can_stop:
                await state.memory.delete_many(response.output)

                full_text = "".join(msg.text for msg in text_messages)
                json_object_pair = find_first_pair(full_text, ("{", "}"))
                final_answer_input = parse_broken_json(json_object_pair.outer) if json_object_pair else None
                if not final_answer_input and not request.final_answer.custom_schema:
                    final_answer_input = {"response": full_text}

                if not final_answer_input:
                    await reasoner.update(requirements=[])
                    force_final_answer_as_tool = True
                    continue

                tool_call_message = MessageToolCallContent(
                    type="tool-call",
                    id=f"call_{generate_random_string(8).lower()}",
                    tool_name=reasoner.final_answer.name,
                    args=to_json(final_answer_input, sort_keys=False),
                )
                tool_call_messages.append(tool_call_message)
                await state.memory.add(AssistantMessage(tool_call_message))

            cycle_found = False
            for tool_call_msg in tool_call_messages:
                tool_call_cycle_checker.register(tool_call_msg)
                if cycle_found := tool_call_cycle_checker.cycle_found:
                    await state.memory.delete_many(response.output)
                    tmp_rules.append(Rule(target=tool_call_msg.tool_name, allowed=False, hidden=False))
                    tool_call_cycle_checker.reset()
                    break

            if not cycle_found:
                for tool_call in await _run_tools(
                    tools=request.allowed_tools,
                    messages=tool_call_messages,
                    context={"state": state.model_dump()},
                ):
                    state.steps.append(
                        RequirementAgentRunStateStep(
                            id=str(uuid.uuid4()),
                            iteration=state.iteration,
                            input=tool_call.input,
                            output=tool_call.output,
                            tool=tool_call.tool,
                            error=tool_call.error,
                        )
                    )

                    if tool_call.error is not None:
                        result = self._templates.tool_error.render(
                            RequirementAgentToolErrorPromptInput(reason=tool_call.error.explain())
                        )
                    else:
                        result = (
                            tool_call.output.get_text_content()
                            if not tool_call.output.is_empty()
                            else self._templates.tool_no_result.render(tool_call=tool_call)
                        )

                    await state.memory.add(
                        ToolMessage(
                            MessageToolResultContent(
                                tool_name=tool_call.tool.name if tool_call.tool else tool_call.msg.tool_name,
                                tool_call_id=tool_call.msg.id,
                                result=result,
                            )
                        )
                    )
                    if tool_call.error is not None:
                        tool_call_retry_counter.use(tool_call.error)

            # handle empty responses for some models
            if not tool_call_messages and not text_messages:
                await state.memory.add(AssistantMessage("\n", {"tempMessage": True}))
            else:
                await state.memory.delete_many(
                    [msg for msg in state.memory.messages if msg.meta.get("tempMessage", False)]
                )

            await run_context.emitter.emit(
                "success",
                RequirementAgentSuccessEvent(state=state, response=response),
            )

        if self._save_intermediate_steps:
            self.memory.reset()
            await self.memory.add_many(state.memory.messages)
        else:
            if user_message is not None:
                await self.memory.add(user_message)

            await self.memory.add_many(extract_last_tool_call_pair(state.memory) or [])

        return RequirementAgentOutput(output=[state.answer], output_structured=state.result, state=state)

    def _create_emitter(self) -> Emitter:
        return Emitter.root().child(
            namespace=["agent", "requirement"], creator=self, events=requirement_agent_event_types
        )

    @property
    def memory(self) -> BaseMemory:
        return self._memory

    @memory.setter
    def memory(self, memory: BaseMemory) -> None:
        self._memory = memory

    @staticmethod
    def _generate_templates(
        overrides: dict[RequirementAgentTemplatesKeys, PromptTemplate[Any] | RequirementAgentTemplateFactory]
        | RequirementAgentTemplates
        | None = None,
    ) -> RequirementAgentTemplates:
        if isinstance(overrides, RequirementAgentTemplates):
            return overrides

        templates = RequirementAgentTemplates()
        if overrides is None:
            return templates

        for name, _info in RequirementAgentTemplates.model_fields.items():
            override: PromptTemplate[Any] | RequirementAgentTemplateFactory | None = overrides.get(name)
            if override is None:
                continue
            elif isinstance(override, PromptTemplate):
                setattr(templates, name, override)
            else:
                setattr(templates, name, override(getattr(templates, name)))
        return templates

    async def clone(self) -> "RequirementAgent":
        cloned = RequirementAgent(
            llm=await self._llm.clone(),
            memory=await self._memory.clone(),
            tools=self._tools.copy(),
            requirements=self._requirements.copy(),
            templates=self._templates.model_dump(),
            tool_call_checker=(
                self._tool_call_checker.config.model_copy()
                if isinstance(self._tool_call_checker, ToolCallChecker)
                else self._tool_call_checker
            ),
            save_intermediate_steps=self._save_intermediate_steps,
            final_answer_as_tool=self._final_answer_as_tool,
            name=self._meta.name,
            description=self._meta.description,
            middlewares=self.middlewares.copy(),
        )
        cloned.emitter = await self.emitter.clone()
        return cloned

    @property
    def meta(self) -> AgentMeta:
        parent = super().meta

        return AgentMeta(
            name=self._meta.name or parent.name,
            description=self._meta.description or parent.description,
            extra_description=self._meta.extra_description or parent.extra_description,
            tools=list(self._tools),
        )

    def _create_tool_call_checker(self) -> ToolCallChecker:
        config = ToolCallCheckerConfig()
        update_model(config, sources=[self._tool_call_checker])

        instance = ToolCallChecker(config)
        instance.enabled = self._tool_call_checker is not False
        return instance

    def _stream_final_answer(
        self, request: RequirementAgentRequest, ctx: RunContext, state: RequirementAgentRunState
    ) -> StreamToolCallMiddleware:
        middleware = StreamToolCallMiddleware(
            request.final_answer,
            "response",  # from the default schema
            match_nested=False,
            force_streaming=False,
        )

        @middleware.emitter.on("update")
        async def send_update(data: StreamToolCallMiddlewareUpdateEvent, meta: EventMeta) -> None:
            await ctx.emitter.emit(
                "final_answer",
                RequirementAgentFinalAnswerEvent(
                    state=state, output=data.output, delta=data.delta, output_structured=data.output_structured
                ),
            )

        return middleware
