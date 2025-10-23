from typing import List, Dict, Any, Optional
from santai_mcp_client.transport import TransportFactory
from santai_mcp_client.models import Tool
import inspect


class MCPClient:
    def __init__(
        self,
        url: Optional[str] = "",
        token: Optional[str] = None,
        transport: Optional[str] = "auto",
        commands: Optional[str] = "",
        args: Optional[List[str]] = None,
        headers: Optional[dict] = None,
    ) -> None:
        self.url = url
        self.token = token
        self.headers: Dict[str, str] = dict(headers or {})
        self.client_kwargs: Dict[str, Any] = {}
        self.commands = commands
        self.args = args or []

        if token:
            self.client_kwargs["auth"] = token

        factory = TransportFactory(
            url=self.url,
            commands=self.commands or "",
            args=self.args,
            headers=self.headers,
            client_kwargs=self.client_kwargs,
        )
        self.client = factory.construct(transport)

    async def list_tools(self):
        retrieved_tools = []

        if hasattr(self.client, "__aenter__") and hasattr(self.client, "__aexit__"):
            async with self.client as client:
                lt = getattr(client, "list_tools")
                retrieved_tools = (
                    await lt() if inspect.iscoroutinefunction(lt) else lt()
                )

        tools: List[Tool] = []
        for t in retrieved_tools or []:
            schema = getattr(t, "inputSchema", None)
            tools.append(
                Tool(
                    name=getattr(t, "name", ""),
                    description=getattr(t, "description", "") or "",
                    input_schema=schema if schema else None,
                )
            )

        self.tools = tools
        return tools

    async def execute_tool(self, tool_name, args):
        if hasattr(self.client, "__aenter__") and hasattr(self.client, "__aexit__"):
            async with self.client as client:
                lt = getattr(client, "call_tool")
                response = (
                    await lt(tool_name, args)
                    if inspect.iscoroutinefunction(lt)
                    else lt()
                )

        result = "".join(chunk.text for chunk in response.content)

        return result
