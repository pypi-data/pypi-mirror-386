from typing import Literal, Dict, Any, List
from dataclasses import dataclass, field
import asyncio

from fastmcp import Client
from fastmcp.client.transports import (
    SSETransport,
    StreamableHttpTransport,
    StdioTransport,
)

TransportKind = Literal["sse", "streamable-http", "stdio", "auto"]


@dataclass(slots=True)
class TransportFactory:
    url: str
    commands: str = ""
    args: List[str] = field(default_factory=list)
    headers: Dict[str, str] = field(default_factory=dict)
    client_kwargs: Dict[str, Any] = field(default_factory=dict)

    def _with(self, **extra_headers: str) -> Dict[str, str]:
        h = dict(self.headers)
        h.update(extra_headers)
        return h

    def _client_from_transport(
        self, transport_obj, connect_timeout=3.0, ping_timeout=3.0
    ) -> Client:
        return Client(transport_obj, **self.client_kwargs)

    def sse(self) -> Client:
        return self._client_from_transport(
            SSETransport(url=self.url, headers=self._with(Accept="text/event-stream"))
        )

    def http(self) -> Client:
        return self._client_from_transport(
            StreamableHttpTransport(
                url=self.url,
                headers=self._with(Accept="application/json, text/event-stream"),
            )
        )

    def stdio(self) -> Client:
        print("we received this command", self.commands)
        print("we received these args", self.args)
        return self._client_from_transport(
            StdioTransport(
                command=self.commands,
                args=self.args,
            )
        )

    def auto(self) -> Client:
        """
        Auto-detect transport by trying SSE first, then HTTP.
        Uses 3.0s connect timeout and 3.0s ping timeout.
        Returns an async context manager that yields the connected client.
        """
        factory = self

        class _AutoClient:
            def __init__(self, _factory: "TransportFactory"):
                self._factory = _factory
                self._cm = None  # underlying Client context manager
                self._client = None  # entered client instance

            async def __aenter__(self):
                last_err = None
                for mode in ("sse", "http"):
                    cm = None
                    try:
                        cm = (
                            self._factory.sse()
                            if mode == "sse"
                            else self._factory.http()
                        )
                        client = await asyncio.wait_for(cm.__aenter__(), timeout=3.0)

                        # If the client exposes ping(), verify the connection quickly
                        if hasattr(client, "ping"):
                            await asyncio.wait_for(client.ping(), timeout=3.0)

                        # Success — keep handles and return the real client
                        self._cm = cm
                        self._client = client
                        return client

                    except Exception as e:
                        last_err = e
                        # Best-effort cleanup for partially opened cm
                        try:
                            if cm is not None:
                                await cm.__aexit__(None, None, None)
                        except Exception:
                            pass
                        # Try next mode
                        continue

                # If neither mode succeeded, raise the last encountered error
                raise last_err or RuntimeError("Auto transport detection failed")

            async def __aexit__(self, exc_type, exc, tb):
                if self._cm is not None:
                    return await self._cm.__aexit__(exc_type, exc, tb)
                return False

        return _AutoClient(factory)

    def construct(self, kind: TransportKind) -> Client:
        if kind == "sse":
            return self.sse()

        if kind == "streamable-http":
            return self.http()

        if kind == "stdio":
            return self.stdio()

        if kind == "auto":
            return self.auto()

        raise ValueError(f"Unknown transport method: {kind!r}")
