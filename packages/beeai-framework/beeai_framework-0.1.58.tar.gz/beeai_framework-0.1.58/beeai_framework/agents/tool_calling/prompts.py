# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from datetime import UTC, datetime

from pydantic import BaseModel

from beeai_framework.template import PromptTemplate


class ToolCallingAgentSystemPromptInput(BaseModel):
    role: str
    instructions: str | None = None


ToolCallingAgentSystemPrompt = PromptTemplate(
    schema=ToolCallingAgentSystemPromptInput,
    functions={"formatDate": lambda data: datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")},
    defaults={"role": "A helpful AI assistant", "instructions": ""},
    template="""Assume the role of {{role}}.
{{#instructions}}

Your instructions are:
{{.}}
{{/instructions}}

When the user sends a message, figure out a solution and provide a final answer to the user by calling the 'final_answer' tool.
Before you call the 'final_answer' tool, ensure that you have gathered sufficient evidence to support the final answer.

# Best practices
- Use markdown syntax to format code snippets, links, JSON, tables, images, and files.
- If the provided task is unclear, ask the user for clarification.
- Do not refer to tools or tool outputs by name when responding.
- Do not call the same tool twice with the similar inputs.

# Date and Time
The current date and time is: {{formatDate}}
You do not need a tool to get the current Date and Time. Use the information available here.
""",  # noqa: E501
)


class ToolCallingAgentTaskPromptInput(BaseModel):
    prompt: str
    context: str | None = None
    expected_output: str | type[BaseModel] | None = None


ToolCallingAgentTaskPrompt = PromptTemplate(
    schema=ToolCallingAgentTaskPromptInput,
    template="""{{#context}}This is the context that you are working with:
{{.}}

{{/context}}
{{#expected_output}}
This is the expected criteria for your output:
{{.}}

{{/expected_output}}
Your task: {{prompt}}
""",
)


class ToolCallingAgentToolErrorPromptInput(BaseModel):
    reason: str


ToolCallingAgentToolErrorPrompt = PromptTemplate(
    schema=ToolCallingAgentToolErrorPromptInput,
    template="""The tool has failed; the error log is shown below. If the tool cannot accomplish what you want, use a different tool or explain why you can't use it.

{{&reason}}""",  # noqa: E501
)


class ToolCallingAgentCycleDetectionPromptInput(BaseModel):
    tool_name: str
    tool_args: str
    final_answer_tool: str


ToolCallingAgentCycleDetectionPrompt = PromptTemplate(
    schema=ToolCallingAgentCycleDetectionPromptInput,
    template="""I can't see your answer. You must use the '{{final_answer_tool}}' tool to send me a message.""",
)
