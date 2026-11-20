"""Connect the agent to GDSFactory+ through its MCP server (gfp-mcp).

When a GDSFactory+ project is open (VS Code extension or GDSFactory+ Cloud workspace),
gfp-mcp exposes tools such as list_cells, build_cells, check_drc, check_lvs and
simulate_component. This module starts gfp-mcp-serve over stdio, lists its tools,
and hands them to the agent with a "gfp_" prefix, so Claude can, for example, run
foundry sign-off DRC with gfp_check_drc on the same design.

If gfp-mcp is not installed or no GDSFactory+ project is running, the agent simply
runs with its local tools.
"""
from __future__ import annotations

import json
import shutil
from contextlib import AsyncExitStack

PREFIX = "gfp_"


class GFPBridge:
    def __init__(self) -> None:
        self._stack = AsyncExitStack()
        self.session = None
        self.tools: list[dict] = []

    async def start(self) -> "GFPBridge":
        if shutil.which("gfp-mcp-serve") is None:
            return self
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        params = StdioServerParameters(command="gfp-mcp-serve", args=[])
        read, write = await self._stack.enter_async_context(stdio_client(params))
        self.session = await self._stack.enter_async_context(ClientSession(read, write))
        await self.session.initialize()
        listed = await self.session.list_tools()
        self.tools = [
            {"name": PREFIX + t.name, "description": f"[GDSFactory+] {t.description or ''}"[:1024],
             "input_schema": t.inputSchema or {"type": "object", "properties": {}}}
            for t in listed.tools
        ]
        return self

    def handles(self, name: str) -> bool:
        return self.session is not None and name.startswith(PREFIX)

    async def call(self, name: str, args: dict) -> str:
        result = await self.session.call_tool(name[len(PREFIX):], args)
        parts = [getattr(c, "text", "") for c in result.content]
        return "\n".join(p for p in parts if p) or json.dumps({"ok": not result.isError})

    async def close(self) -> None:
        await self._stack.aclose()
