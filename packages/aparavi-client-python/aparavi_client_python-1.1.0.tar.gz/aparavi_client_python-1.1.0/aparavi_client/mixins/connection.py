# MIT License
#
# Copyright (c) 2025 Aparavi Corporation
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Connection Management for Aparavi Client.

This module handles connecting to and disconnecting from Aparavi servers.
It manages the WebSocket connection lifecycle and provides status checking.

The connection system automatically handles:
- WebSocket connection establishment
- Authentication with your API key
- Connection status tracking
- Automatic reconnection on disconnects (when persist=True)
- Graceful disconnection and cleanup

Usage:
    # Manual connection management
    client = AparaviClient(auth="your_api_key", uri="https://eaas.aparavi.com")
    await client.connect()

    # Check if connected
    if client.is_connected():
        # Do work with the client
        pass

    await client.disconnect()

    # Automatic connection management (recommended)
    async with AparaviClient(auth="your_api_key") as client:
        # Client automatically connects here
        # Do work with connected client
        pass
    # Client automatically disconnects here

    # Persistent connection with auto-reconnect
    client = AparaviClient(auth="your_api_key", persist=True, reconnect_delay=2.0)
    await client.connect()
    # Connection will automatically reconnect if dropped
"""

import asyncio
from typing import Any, Dict, Optional
from ..core import DAPClient


class ConnectionMixin(DAPClient):
    """
    Handles connection and disconnection to Aparavi servers.

    This mixin provides the fundamental connection management capabilities
    for the Aparavi client. It manages WebSocket connections, handles
    authentication, and tracks connection status.

    Key Features:
    - Establishes secure WebSocket connections to Aparavi servers
    - Authenticates using your API key or access token
    - Tracks connection status for reliable operations
    - Automatic reconnection on disconnect (when persist=True)
    - Provides graceful connection cleanup
    - Supports both manual and automatic connection management

    This is automatically included when you use AparaviClient, so you can
    call client.connect() and client.disconnect() directly without needing
    to import this mixin.
    """

    def __init__(self, persist: bool = False, reconnect_delay: float = 1.0, **kwargs):
        """
        Initialize connection management.

        Args:
            persist: Enable automatic reconnection on disconnect
            reconnect_delay: Seconds to wait before reconnection attempt
            **kwargs: Additional arguments passed to parent class
        """
        super().__init__(**kwargs)
        self._persist = persist
        self._reconnect_delay = reconnect_delay
        self._manual_disconnect = False
        self._reconnect_task: Optional[asyncio.Task] = None

    def is_connected(self):
        """
        Check if the client is currently connected to the Aparavi server.

        Use this to verify connection status before performing operations
        that require server communication. A connected client can execute
        pipelines, send data, and perform chat operations.

        Returns:
            bool: True if connected and ready to use, False if disconnected

        Example:
            if client.is_connected():
                # Safe to perform operations
                token = await client.use(filepath="pipeline.json")
                await client.send(token, "Hello, world!")
            else:
                print("Client is not connected. Call await client.connect() first.")
        """
        return self._transport.is_connected()

    async def on_connected(self, connection_info: Optional[str] = None) -> None:
        """
        Handle connection established event.

        Resets manual disconnect flag and delegates to parent.
        """
        self._manual_disconnect = False
        await super().on_connected(connection_info)

    async def on_disconnected(self, reason: Optional[str] = None, has_error: bool = False) -> None:
        """
        Handle disconnection event.

        Delegates to parent and schedules reconnection if persist is enabled.
        """
        await super().on_disconnected(reason, has_error)

        # Schedule reconnection if persist is enabled and not a manual disconnect
        if self._persist and not self._manual_disconnect:
            self._schedule_reconnect()

    def _schedule_reconnect(self) -> None:
        """Schedule a reconnection attempt after the configured delay."""
        # Cancel any existing reconnect task
        if self._reconnect_task and not self._reconnect_task.done():
            self._reconnect_task.cancel()

        self._debug_message(f'Scheduling reconnection in {self._reconnect_delay}s')
        self._reconnect_task = asyncio.create_task(self._attempt_reconnect())

    async def _attempt_reconnect(self) -> None:
        """Attempt to reconnect after delay."""
        await asyncio.sleep(self._reconnect_delay)

        if self._persist and not self._manual_disconnect:
            self._debug_message('Attempting to reconnect...')
            try:
                await super().connect()
                self._debug_message('Reconnection successful')
            except Exception as e:
                self._debug_message(f'Reconnection failed: {e}')
                # Will schedule another attempt via on_disconnected

    async def connect(self) -> None:
        """
        Connect to the Aparavi server.

        Must be called before executing pipelines or other operations.
        In persist mode, enables automatic reconnection.

        Examples:
            # Manual connection management
            await client.connect()
            try:
                # do work
                pass
            finally:
                await client.disconnect()

            # Automatic connection management (preferred)
            async with client:
                # connection automatically managed
                pass
        """
        self._manual_disconnect = False

        # If we are already connected, disconnect first
        if self.is_connected():
            await self.disconnect()

        # Call the dap client function
        await super().connect()

    async def disconnect(self) -> None:
        """
        Disconnect from the Aparavi server and stop automatic reconnection.

        Should be called when finished with the client to clean up resources.
        Context managers handle this automatically.
        """
        self._manual_disconnect = True

        # Cancel any pending reconnection
        if self._reconnect_task and not self._reconnect_task.done():
            self._reconnect_task.cancel()
            self._reconnect_task = None

        # Call the dap client function
        await super().disconnect()

    async def request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a request to the Aparavi server.
        """
        # Delegate to parent class for actual request processing
        return await super().request(request)
