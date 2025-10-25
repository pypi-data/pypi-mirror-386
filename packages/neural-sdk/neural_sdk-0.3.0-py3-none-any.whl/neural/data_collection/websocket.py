import json
from collections.abc import AsyncGenerator
from typing import Any

import websockets

from .base import DataSource


class WebSocketSource(DataSource):
    """Data source for WebSocket streams."""

    def __init__(
        self,
        name: str,
        uri: str,
        headers: dict[str, str] | None = None,
        config: dict[str, Any] | None = None,
    ):
        super().__init__(name, config)
        self.uri = uri
        self.headers = headers or {}
        self.websocket = None

    async def connect(self) -> None:
        """Connect to the WebSocket."""
        try:
            self.websocket = await websockets.connect(self.uri, extra_headers=self.headers)
            self._connected = True
        except Exception as e:
            raise ConnectionError(f"Failed to connect to {self.uri}: {e}") from e

    async def disconnect(self) -> None:
        """Close the WebSocket connection."""
        if self.websocket:
            await self.websocket.close()
        self._connected = False

    async def collect(self) -> AsyncGenerator[dict[str, Any], None]:
        """Listen for messages from the WebSocket."""
        if not self.websocket:
            raise RuntimeError("WebSocket not connected")

        async for message in self.websocket:
            try:
                # Assume JSON messages
                data = json.loads(message)
                yield data
            except json.JSONDecodeError:
                # If not JSON, yield as text
                yield {"message": message}
            except Exception as e:
                print(f"Error processing message from {self.name}: {e}")
