# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from abc import abstractmethod
from collections.abc import AsyncGenerator, Callable
from functools import cached_property
from typing import Any, ClassVar, Literal, Self

from pydantic import BaseModel, ConfigDict, InstanceOf, TypeAdapter, ValidationError
from typing_extensions import TypedDict, TypeVar, Unpack, override

from beeai_framework.backend.constants import ProviderName
from beeai_framework.backend.errors import ChatModelError
from beeai_framework.backend.events import (
    ChatModelErrorEvent,
    ChatModelNewTokenEvent,
    ChatModelStartEvent,
    ChatModelSuccessEvent,
    chat_model_event_types,
)
from beeai_framework.backend.message import AnyMessage, AssistantMessage, MessageToolCallContent
from beeai_framework.backend.types import (
    ChatModelCache,
    ChatModelInput,
    ChatModelOutput,
    ChatModelParameters,
    ChatModelToolChoice,
)
from beeai_framework.backend.utils import (
    filter_tools_by_tool_choice,
    generate_tool_union_schema,
    load_model,
    parse_broken_json,
    parse_model,
)
from beeai_framework.cache.null_cache import NullCache
from beeai_framework.context import RunContext, RunMiddlewareType
from beeai_framework.emitter import Emitter
from beeai_framework.logger import Logger
from beeai_framework.retryable import Retryable, RetryableConfig, RetryableInput
from beeai_framework.runnable import Runnable, RunnableOptions, runnable_entry
from beeai_framework.tools.tool import AnyTool, Tool
from beeai_framework.utils import AbortController, ModelLike
from beeai_framework.utils.asynchronous import to_async_generator
from beeai_framework.utils.dicts import exclude_keys, exclude_non_annotated
from beeai_framework.utils.lists import cast_list
from beeai_framework.utils.models import WrappedRootModel, to_model, update_model
from beeai_framework.utils.strings import generate_random_string, to_json

T = TypeVar("T", bound=BaseModel)
TTool = TypeVar("TTool", bound=AnyTool)
ChatModelFinishReason: Literal["stop", "length", "function_call", "content_filter", "null"]
ToolChoiceType = Literal["required", "none", "single", "auto"]
logger = Logger(__name__)


class ChatModelKwargs(TypedDict, total=False):
    tool_call_fallback_via_response_format: bool
    model_supports_tool_calling: bool
    allow_parallel_tool_calls: bool
    ignore_parallel_tool_calls: bool
    use_strict_tool_schema: bool
    use_strict_model_schema: bool
    supports_top_level_unions: bool
    parameters: InstanceOf[ChatModelParameters]
    cache: InstanceOf[ChatModelCache]
    settings: dict[str, Any]
    middlewares: list[RunMiddlewareType]
    tool_choice_support: set[ToolChoiceType]

    __pydantic_config__ = ConfigDict(extra="forbid", arbitrary_types_allowed=True)  # type: ignore


class ChatModelOptions(RunnableOptions, total=False):
    """Optional options for ChatModel's run method."""

    tools: list[AnyTool] | None
    """Tools available to the model."""

    tool_choice: ChatModelToolChoice | None
    """Controls how an LLM selects and uses tools (auto, required, none, tool name)."""

    max_retries: int | None
    """
    Maximum number of retries.
    """

    stop_sequences: list[str] | None
    """
    Stop words where the model should stop generation.
    """

    response_format: dict[str, Any] | type[BaseModel] | None
    """
    Structured output format.
    """

    validate_response_format: bool | None
    """
    Whether the generated output should be validated against the given response format.
    """

    stream: bool | None
    """
    Flag that indicates whether streaming is enabled.
    """

    parallel_tool_calls: bool | None
    """
    Flag that indicates if concurrent tool call is enabled.
    """

    max_tokens: int | None
    """
    Model parameter that limits the maximum number of generated tokens.
    """

    frequency_penalty: float | None
    """
    Model parameter that discourages the repetition of words by decreasing the likelihood of a token being selected.
    """

    temperature: float | None
    """
    Model paramater that controls the randomness of the generated text.
    """

    top_p: float | None
    """
    Model parameter (nucleous sampling) that decides how many possible words to consider.
    """

    top_k: int | None
    """
    Model parameter that restricts the pool of possible next words to a fixed number of the most probable tokens.
    """

    n: int | None
    """
    Model parameter that controls the number of model completions (generations).
    """

    presence_penalty: float | None
    """
    Model parameter that controls how much the model penalizes new tokens that are already present in the conversation.
    """

    seed: int | None
    """
    Model parameter that controls deterministic sampling.
    """

    stream_partial_tool_calls: bool | None
    """
    Generated chunks will be streamed without validation of the produced tool calls.
    """


_ChatModelKwargsAdapter = TypeAdapter(ChatModelKwargs)


class ChatModel(Runnable[ChatModelOutput]):
    tool_choice_support: ClassVar[set[ToolChoiceType]] = {"required", "none", "single", "auto"}
    tool_call_fallback_via_response_format: bool
    model_supports_tool_calling: bool
    use_strict_model_schema: bool
    use_strict_tool_schema: bool

    @property
    @abstractmethod
    def model_id(self) -> str:
        pass

    @property
    @abstractmethod
    def provider_id(self) -> ProviderName:
        pass

    def __init__(self, **kwargs: Unpack[ChatModelKwargs]) -> None:
        super().__init__(middlewares=kwargs.get("middlewares", []))
        self._settings = kwargs.get("settings", {})
        self._settings.update(**exclude_non_annotated(kwargs, ChatModelKwargs))

        kwargs = _ChatModelKwargsAdapter.validate_python(kwargs)

        parameters = type(self).get_default_parameters()
        update_model(parameters, sources=[kwargs.get("parameters")])
        self.parameters = parameters

        self.cache = kwargs.get("cache", NullCache[list[ChatModelOutput]]())
        self.tool_call_fallback_via_response_format = kwargs.get("tool_call_fallback_via_response_format", True)
        self.model_supports_tool_calling = kwargs.get("model_supports_tool_calling", True)
        self.allow_parallel_tool_calls = kwargs.get("allow_parallel_tool_calls", False)
        self.ignore_parallel_tool_calls = kwargs.get("ignore_parallel_tool_calls", False)
        self.use_strict_tool_schema = kwargs.get("use_strict_tool_schema", True)
        self.use_strict_model_schema = kwargs.get("use_strict_model_schema", False)
        self.supports_top_level_unions = kwargs.get("supports_top_level_unions", True)

        custom_tool_choice_support = kwargs.get("tool_choice_support")
        self._tool_choice_support: set[ToolChoiceType] = (
            custom_tool_choice_support
            if custom_tool_choice_support is not None
            else type(self).tool_choice_support.copy()
        )

    @cached_property
    def emitter(self) -> Emitter:
        return self._create_emitter()

    def _create_emitter(self) -> Emitter:
        return Emitter.root().child(
            namespace=["backend", self.provider_id, "chat"],
            creator=self,
            events=chat_model_event_types,
        )

    @abstractmethod
    async def _create(
        self,
        input: ChatModelInput,
        run: RunContext,
    ) -> ChatModelOutput:
        raise NotImplementedError

    @abstractmethod
    def _create_stream(
        self,
        input: ChatModelInput,
        run: RunContext,
    ) -> AsyncGenerator[ChatModelOutput]:
        raise NotImplementedError

    @override
    @runnable_entry
    async def run(self, input: list[AnyMessage], /, **kwargs: Unpack[ChatModelOptions]) -> ChatModelOutput:
        """Execute the chat model.

        Args:
            input: The input to the chat model
            tools: Tools available to the model
            tool_choice: Controls how an LLM selects and uses tools (auto, required, none, tool name)
            max_retries: Maximum number of retries
            stop_sequences: Stop words where the model should stop generation
            response_format: Structured output format
            stream: Flag that indicates whether streaming is enabled
            parallel_tool_calls: Flag that indicates if concurrent tool call is enabled
            max_tokens: Limits the maximum number of generated tokens
            frequency_penalty: Discourages the repetition of words
            temperature: Controls the randomness of the generated text
            top_p: Sampling parameter that decides how many possible words to consider
            top_k: Restricts the pool of possible next words
            n: Controls the number of model completions (generations)
            presence_penalty: Controls how much the model penalizes previously generated tokens
            seed: Controls deterministic sampling
            signal: The chat model abort signal
            context: A dictionary that can be used to pass additional context to the chat model

        Returns:
            The chat model output.
        """
        tools = kwargs.get("tools")
        tool_choice = kwargs.get("tool_choice")
        response_format = kwargs.get("response_format")
        stream = kwargs.get("stream", self.parameters.stream)
        parallel_tool_calls = kwargs.get("parallel_tool_calls")

        force_tool_call_via_response_format = self._force_tool_call_via_response_format(
            tool_choice=tool_choice,
            tools=tools or [],
            has_custom_response_format=bool(response_format),
        )

        if parallel_tool_calls is None:
            parallel_tool_calls = self.allow_parallel_tool_calls and not self.ignore_parallel_tool_calls
        else:
            parallel_tool_calls = parallel_tool_calls and not self.ignore_parallel_tool_calls

        response_format_final, response_format_schema = (
            generate_tool_union_schema(
                filter_tools_by_tool_choice(tools, tool_choice),
                strict=self.use_strict_model_schema,
                allow_top_level_union=self.supports_top_level_unions,
                allow_parallel_tool_calls=parallel_tool_calls,
            )
            if force_tool_call_via_response_format and tools
            else (response_format, None)
        )

        validate_response_format = kwargs.get("validate_response_format")
        model_input = ChatModelInput(
            messages=input,
            tools=tools if self.model_supports_tool_calling else None,
            response_format=response_format_final,
            validate_response_format=True if validate_response_format is None else validate_response_format,
            stream=stream if stream is not None else self.parameters.stream,
            **exclude_keys(dict(kwargs), {"tools", "response_format", "stream", "validate_response_format"}),
        )

        context = RunContext.get()
        cache_key = self.cache.generate_key(model_input, {"messages": [m.to_plain() for m in model_input.messages]})
        cache_hit = await self.cache.get(cache_key)

        try:
            await context.emitter.emit("start", ChatModelStartEvent(input=model_input))
            chunks: list[ChatModelOutput] = []

            if model_input.stream:
                generator = to_async_generator(cache_hit) if cache_hit else self._create_stream(model_input, context)
                abort_controller: AbortController = AbortController()
                async for value in generator:
                    chunks.append(value)
                    await context.emitter.emit(
                        "new_token", ChatModelNewTokenEvent(value=value, abort=lambda: abort_controller.abort())
                    )
                    if abort_controller.signal.aborted:
                        break

                if not cache_hit:
                    await self.cache.set(cache_key, chunks)
                result = ChatModelOutput.from_chunks(chunks)
            else:
                if cache_hit:
                    result = cache_hit[0].model_copy()
                else:
                    result = await Retryable(
                        RetryableInput(
                            executor=lambda _: self._create(model_input, context),
                            config=RetryableConfig(
                                max_retries=(
                                    model_input.max_retries
                                    if model_input is not None and model_input.max_retries is not None
                                    else 0
                                ),
                                signal=context.signal,
                            ),
                        )
                    ).get()

                    await self.cache.set(cache_key, [result])

            if force_tool_call_via_response_format and not result.get_tool_calls():
                assert response_format_schema and issubclass(response_format_schema, BaseModel)

                final_message = AssistantMessage.from_chunks(result.output)
                final_message.content.clear()

                text = result.get_text_content()
                tool_calls_raw = parse_broken_json(text)
                if isinstance(tool_calls_raw, list) and self.ignore_parallel_tool_calls:
                    tool_calls_raw = tool_calls_raw[0]

                try:
                    tool_calls = response_format_schema.model_validate(tool_calls_raw)
                    if isinstance(tool_calls, WrappedRootModel):
                        tool_calls = tool_calls.item
                except ValidationError as ex:
                    raise ChatModelError("Failed to produce a valid tool call.") from ex

                for tool_call in cast_list(tool_calls.model_dump()):
                    if not tool_call or not tool_call.get("name") or tool_call.get("parameters") is None:
                        raise ChatModelError(
                            "Failed to produce a valid tool call.\n"
                            "Try to increase max new tokens for your chat model.\n"
                            f"Generated output: {text}",
                        )

                    tool_call_content = MessageToolCallContent(
                        id=f"call_{generate_random_string(8).lower()}",
                        tool_name=tool_call["name"],
                        args=to_json(tool_call["parameters"], sort_keys=False, indent=None),
                    )
                    final_message.content.append(tool_call_content)

                result.output.clear()
                result.output.append(final_message)

            while self.ignore_parallel_tool_calls and len(result.get_tool_calls()) > 1:
                tool_call_to_remove = result.get_tool_calls()[-1]
                for msg in reversed(result.output):
                    if isinstance(msg, AssistantMessage):
                        msg.content.remove(tool_call_to_remove)
                        if not msg.content:
                            result.output.remove(msg)
                        break

            self._assert_tool_response(input=model_input, output=result)

            await context.emitter.emit("success", ChatModelSuccessEvent(value=result))
            return result
        except Exception as ex:
            error = ChatModelError.ensure(ex, model=self)
            if cache_hit:
                await self.cache.delete(cache_key)
            await context.emitter.emit("error", ChatModelErrorEvent(input=model_input, error=error))
            raise error
        finally:
            await context.emitter.emit("finish", None)

    def config(
        self,
        *,
        parameters: ChatModelParameters | Callable[[ChatModelParameters], ChatModelParameters] | None = None,
        cache: ChatModelCache | Callable[[ChatModelCache], ChatModelCache] | None = None,
    ) -> None:
        if cache is not None:
            self.cache = cache(self.cache) if callable(cache) else cache

        if parameters is not None:
            self.parameters = parameters(self.parameters) if callable(parameters) else parameters

    @staticmethod
    def from_name(
        name: str | ProviderName,
        options: ModelLike[ChatModelParameters] | None = None,
        /,
        **kwargs: Any,
    ) -> "ChatModel":
        parsed_model = parse_model(name)
        TargetChatModel = load_model(parsed_model.provider_id, "chat")  # type: ignore # noqa: N806
        if options and isinstance(options, ChatModelParameters):
            kwargs["parameters"] = to_model(ChatModelParameters, options)
        elif options:
            kwargs.update(options)

        return TargetChatModel(parsed_model.model_id, **kwargs)  # type: ignore

    def _force_tool_call_via_response_format(
        self,
        *,
        tool_choice: ChatModelToolChoice | None,
        tools: list[AnyTool],
        has_custom_response_format: bool,
    ) -> bool:
        if (
            not tools
            or tool_choice == "none"
            or tool_choice == "auto"
            or tool_choice is None
            or has_custom_response_format
            or not self.tool_call_fallback_via_response_format
        ):
            return False

        tool_choice_supported = not tool_choice or (
            "single" in self._tool_choice_support
            if isinstance(tool_choice, Tool)
            else tool_choice in self._tool_choice_support
        )

        return not self.model_supports_tool_calling or not tool_choice_supported

    async def clone(self) -> Self:
        cloned = type(self)(
            parameters=ChatModelParameters(**self.parameters.model_dump())
            if self.parameters
            else ChatModelParameters(),
            cache=await self.cache.clone() if self.cache else NullCache[list[ChatModelOutput]](),
            tool_call_fallback_via_response_format=self.tool_call_fallback_via_response_format,
            model_supports_tool_calling=self.model_supports_tool_calling,
            settings=self._settings.copy(),
            use_strict_model_schema=self.use_strict_model_schema,
            use_strict_tool_schema=self.use_strict_tool_schema,
            tool_choice_support=self._tool_choice_support.copy(),
        )
        return cloned

    @classmethod
    def get_default_parameters(cls) -> ChatModelParameters:
        return ChatModelParameters(temperature=0)

    def _assert_tool_response(self, *, input: ChatModelInput, output: ChatModelOutput) -> None:
        if input.tool_choice is None or input.tool_choice == "auto" or self.model_supports_tool_calling is False:
            return

        tool_calls = output.get_tool_calls()
        parallel_tool_calls = (
            input.parallel_tool_calls if input.parallel_tool_calls is not None else self.allow_parallel_tool_calls
        )

        if not parallel_tool_calls and len(tool_calls) > 1:
            raise ChatModelError(
                "The model produced more than one tool call, but parallel tool calls are disabled\n."
                "Consider enabling parallel tool calls by setting 'model.allow_parallel_tool_calls' to True.",
            )

        if input.tool_choice == "none" and tool_calls:
            raise _create_tool_choice_error(
                "The model generated a tool call, but 'tool_choice' was set to 'none'.",
                input_tool_choice=input.tool_choice,
                model=self,
            )

        if isinstance(input.tool_choice, Tool):
            if not tool_calls:
                raise _create_tool_choice_error(
                    f"The model was required to produce a tool call for the '{input.tool_choice.name}' tool, "
                    f"but no tool calls were generated.",
                    input_tool_choice=input.tool_choice,
                    model=self,
                )

            for tool_call in tool_calls:
                if tool_call.tool_name != input.tool_choice.name:
                    raise _create_tool_choice_error(
                        f"The model was required to produce a tool call for the '{input.tool_choice.name}' tool, "
                        f"but generated one for '{tool_call.tool_name}' instead.",
                        input_tool_choice=input.tool_choice,
                        model=self,
                    )

        if input.tool_choice == "required" and input.tools and not output.get_tool_calls():
            raise _create_tool_choice_error(
                "The model was required to produce a tool call, but no tool calls were generated.",
                input_tool_choice=input.tool_choice,
                model=self,
            )

        if input.tools:
            available_tools: set[str] = {t.name for t in input.tools}
            for tool_call in output.get_tool_calls():
                if tool_call.tool_name not in available_tools:
                    raise ChatModelError(
                        f"The model generated a tool call for an unknown tool '{tool_call.tool_name}'.\n"
                        f"Available tools: {','.join(available_tools)}",
                    )


def _create_tool_choice_error(message: str, *, input_tool_choice: str | AnyTool, model: ChatModel) -> ChatModelError:
    input_tool_choice_str = "single" if isinstance(input_tool_choice, Tool) else input_tool_choice
    tool_choice_support: set[str] = set(model._tool_choice_support)
    tool_choice_support.discard(input_tool_choice_str)
    tool_choices_set_str = (
        "{" + ", ".join(f'"{t}"' for t in tool_choice_support) + "}" if tool_choice_support else set()
    )

    model_class = type(model).__name__
    provider = f"{model.provider_id}:{model.model_id}"

    return ChatModelError(
        f"{message}\n\n"
        f"This may occur if the target provider does not support 'tool_choice={{\"{input_tool_choice_str}\"}}', "
        f"but the framework is configured to support it. "
        f"To resolve this, update the supported values for the 'tool_choice' parameter.\n\n"
        f"Use one of the provided options:\n"
        f"1. ChatModel.from_name('{provider}', tool_choice_support={tool_choices_set_str})\n"
        f"2. model = {model_class}(...) \n"
        f"   model.tool_choice_support = {tool_choices_set_str}\n"
        f'3. {model_class}.tool_choice_support.discard("{input_tool_choice_str}")\n',
    )
