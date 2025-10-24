# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
from typing import Any, Self

from beeai_framework.tools import ToolError
from beeai_framework.tools.mcp.utils.session_provider import MCPClient, MCPSessionProvider

try:
    from mcp import ClientSession
    from mcp.types import CallToolResult
    from mcp.types import Tool as MCPToolInfo
except ModuleNotFoundError as e:
    raise ModuleNotFoundError(
        "Optional module [mcp] not found.\nRun 'pip install \"beeai-framework[mcp]\"' to install."
    ) from e

from pydantic import BaseModel

from beeai_framework.context import RunContext
from beeai_framework.emitter import Emitter
from beeai_framework.logger import Logger
from beeai_framework.tools.tool import Tool
from beeai_framework.tools.types import JSONToolOutput, ToolRunOptions
from beeai_framework.utils.models import JSONSchemaModel
from beeai_framework.utils.strings import to_json, to_safe_word

logger = Logger(__name__)

__all__ = ["MCPClient", "MCPTool"]


class MCPTool(Tool[BaseModel, ToolRunOptions, JSONToolOutput]):
    """Tool implementation for Model Context Protocol."""

    def __init__(self, session: ClientSession, tool: MCPToolInfo, **options: int) -> None:
        """Initialize MCPTool with client and tool configuration."""
        super().__init__(options)
        self._session = session
        self._tool = tool

    @property
    def name(self) -> str:
        return self._tool.name

    @property
    def description(self) -> str:
        return self._tool.description or "No available description, use the tool based on its name and schema."

    @property
    def input_schema(self) -> type[BaseModel]:
        return JSONSchemaModel.create(self.name, self._tool.inputSchema)

    def _create_emitter(self) -> Emitter:
        return Emitter.root().child(
            namespace=["tool", "mcp", to_safe_word(self._tool.name)],
            creator=self,
        )

    async def _run(self, input_data: Any, options: ToolRunOptions | None, context: RunContext) -> JSONToolOutput:
        """Execute the tool with given input."""
        logger.debug(f"Executing tool {self._tool.name} with input: {input_data}")
        result: CallToolResult = await self._session.call_tool(
            name=self._tool.name, arguments=input_data.model_dump(exclude_none=True, exclude_unset=True)
        )
        logger.debug(f"Tool result: {result}")

        data_result: Any = None
        if result.structuredContent is not None:
            data_result = result.structuredContent
        else:
            data_result = result.content[0] if len(result.content) == 1 else result.content

        if result.isError:
            raise ToolError(to_json(data_result, indent=4, sort_keys=False))

        return JSONToolOutput(data_result)

    @classmethod
    async def from_client(cls, client: MCPClient | ClientSession) -> list["MCPTool"]:
        if isinstance(client, ClientSession):
            return await cls.from_session(client)

        manager = MCPSessionProvider(client)
        session = await manager.session()
        instance = await cls.from_session(session)
        manager.refs += len(instance)
        return instance

    def __del__(self) -> None:
        MCPSessionProvider.destroy_by_session(self._session)

    @classmethod
    async def from_session(cls, session: ClientSession) -> list["MCPTool"]:
        tools_result = await session.list_tools()
        return [MCPTool(session, tool) for tool in tools_result.tools]

    async def clone(self) -> Self:
        cloned = await super().clone()
        cloned._session = self._session
        cloned._tool = self._tool.model_copy()
        return cloned
