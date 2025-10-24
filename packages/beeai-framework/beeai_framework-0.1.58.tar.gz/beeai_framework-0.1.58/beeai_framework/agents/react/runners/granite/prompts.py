# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from datetime import UTC, datetime

from beeai_framework.agents.react.runners.default.prompts import (
    AssistantPromptTemplateInput,
    SchemaErrorTemplateInput,
    SystemPromptTemplateInput,
    ToolErrorTemplateInput,
    ToolInputErrorTemplateInput,
    ToolNotFoundErrorTemplateInput,
    UserPromptTemplateInput,
)
from beeai_framework.template import PromptTemplate

GraniteUserPromptTemplate = PromptTemplate(schema=UserPromptTemplateInput, template="{{input}}")

GraniteAssistantPromptTemplate = PromptTemplate(
    schema=AssistantPromptTemplateInput,
    template="{{#thought}}Thought: {{.}}\n{{/thought}}{{#tool_name}}Tool Name: {{.}}\n{{/tool_name}}{{#tool_input}}Tool Input: {{&.}}\n{{/tool_input}}{{#final_answer}}Final Answer: {{.}}{{/final_answer}}",  # noqa: E501
)

GraniteSystemPromptTemplate = PromptTemplate(
    schema=SystemPromptTemplateInput,
    functions={
        "formatDate": lambda data: datetime.now(tz=UTC).strftime("%A, %B %d, %Y at %I:%M:%S %p"),
    },
    template="""You are an AI assistant.
When the user sends a message figure out a solution and provide a final answer.
{{#tools.0}}
You have access to a set of tools that can be used to retrieve information and perform actions.
Pay close attention to the tool description to determine if a tool is useful in a particular context.
{{/tools.0}}

# Communication structure
You communicate only in instruction lines. Valid instruction lines are 'Thought' followed by 'Tool Name' and then 'Tool Input', or 'Thought' followed by 'Final Answer'

Line starting 'Thought: ' The assistant's response always starts with a thought, this is a single line where the assistant thinks about the user's message and describes in detail what it should do next.
{{#tools.0}}
In a 'Thought: ', the assistant should determine if a Tool Call is necessary to get more information or perform an action, or if the available information is sufficient to provide the Final Answer.
If a tool needs to be called and is available, the assistant will produce a tool call:
Line starting 'Tool Name: ' name of the tool that you want to use.
Line starting 'Tool Input: ' JSON formatted tool arguments adhering to the selected tool parameters schema i.e. {"arg1":"value1", "arg2":"value2"}.
After a 'Tool Input: ' the next message will contain a tool response. The next output should be a 'Thought: ' where the assistant thinks about the all the information it has available, and what it should do next (e.g. try the same tool with a different input, try a different tool, or proceed with answering the original user question).
{{/tools.0}}
Once enough information is available to provide the Final Answer, the last line in the message needs to be:
Line starting 'Final Answer: ' followed by a concise and clear answer to the original message.

# Best practices
- Use markdown syntax for formatting code snippets, links, JSON, tables, images, files.
{{#tools.0}}
- Do not attempt to use a tool that is not listed in available tools. This will cause an error.
- Make sure that tool input is in the correct format and contains the correct arguments.
{{/tools.0}}
- When the message is unclear, respond with a line starting with 'Final Answer:' followed by a request for additional information needed to solve the problem.
- When the user wants to chitchat instead, always respond politely.

# Date and Time
The current date and time is: {{formatDate}}
{{#tools.0}}
You do not need a tool to get the current Date and Time. Use the information available here.
{{/tools.0}}

{{#instructions}}
# Additional instructions
{{.}}
{{/instructions}}
""",  # noqa: E501
)

GraniteToolNotFoundErrorTemplate = PromptTemplate(
    schema=ToolNotFoundErrorTemplateInput,
    template="""The tool does not exist!
{{#tools.length}}
Use one of the following tools: {{#trim}}{{#tools}}{{name}},{{/tools}}{{/trim}}
{{/tools.length}}""",
)

GraniteToolInputErrorTemplate = PromptTemplate(
    schema=ToolInputErrorTemplateInput,
    template="""{{&reason}}

HINT: If you're convinced that the input was correct but the tool cannot process it then use a different tool or say I don't know.""",  # noqa: E501
)

GraniteToolErrorTemplate = PromptTemplate(
    schema=ToolErrorTemplateInput,
    template="""The tool has failed; the error log is shown below. If the tool cannot accomplish what you want, use a different tool or explain why you can't use it.

{{&reason}}""",  # noqa: E501
)

GraniteSchemaErrorTemplate = PromptTemplate(
    schema=SchemaErrorTemplateInput,
    template="""Error: The generated response does not adhere to the communication structure mentioned in the system prompt.
You communicate only in instruction lines. Valid instruction lines are 'Thought' followed by 'Tool Name' and then 'Tool Input' or 'Thought' followed by 'Final Answer'.""",  # noqa: E501
)
