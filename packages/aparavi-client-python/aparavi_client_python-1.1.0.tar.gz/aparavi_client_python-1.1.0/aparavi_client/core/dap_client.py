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
Debug Adapter Protocol (DAP) Client Implementation.

This module provides the DAP client implementation that handles communication
with Aparavi servers using the Debug Adapter Protocol. It manages connection
lifecycle, request/response correlation, and message handling.

This is an internal implementation detail that supports the higher-level
Aparavi client functionality. Most users won't need to interact with this
directly - it's used internally by AparaviClient for server communication.

Key Features:
- WebSocket-based communication with servers
- Request/response correlation using sequence numbers
- Connection lifecycle management
- Message serialization and deserialization
- Error handling and recovery
"""

import asyncio
from typing import Dict, Any, Optional
from .dap_base import DAPBase


class DAPClient(DAPBase):
    """
    DAP (Debug Adapter Protocol) client for communicating with Aparavi servers.

    This class implements the client side of the DAP communication protocol,
    handling connection management, message correlation, and protocol compliance.
    It provides the underlying communication infrastructure used by the
    higher-level Aparavi client functionality.

    Key Responsibilities:
    - Establishing and maintaining connections to DAP servers
    - Correlating requests with their responses using sequence numbers
    - Handling connection events and state changes
    - Managing the message sending and receiving lifecycle
    - Providing error handling and recovery mechanisms

    This is used internally by AparaviClient and its mixins to communicate
    with Aparavi servers reliably and efficiently.
    """

    def __init__(self, **kwargs) -> None:
        """
        Initialize the DAP client infrastructure.

        Sets up the client communication system, initializes request/response
        correlation, and prepares connection state management.

        Args:
            **kwargs: Configuration parameters including transport setup
        """
        # Initialize parent class for DAP functionality
        super().__init__(**kwargs)

        # Request/response correlation system for async operations
        self._pending_requests: Dict[int, asyncio.Future] = {}

    async def _send(self, message: Dict[str, Any]) -> None:
        """
        Send a message to the DAP server through the transport layer.

        Args:
            message: The DAP message to send
        """
        return await self._transport.send(message)

    async def on_connected(self, connection_info: Optional[str] = None) -> None:
        """
        Handle connection established event.

        Called when the transport layer successfully connects to the server.
        Updates connection state and notifies parent classes.

        Args:
            connection_info: Optional connection details from transport
        """
        await super().on_connected(connection_info)

    async def on_disconnected(self, reason: Optional[str] = None, has_error: bool = False) -> None:
        """
        Handle disconnection event and clean up pending requests.

        Called when the transport layer disconnects from the server.
        Fails all pending requests and cleans up connection state.

        Args:
            reason: Optional reason for disconnection
            has_error: Whether disconnection was due to error
        """
        # Fail all pending requests since connection is lost
        connection_error = ConnectionError(reason)

        for seq, future in self._pending_requests.items():
            if not future.done():
                future.set_exception(connection_error)

        # Clear pending requests
        self._pending_requests.clear()

        # Notify parent classes
        await super().on_disconnected(reason, has_error)

    async def on_receive(self, message: Dict[str, Any]) -> None:
        """
        Handle received messages from the transport layer.

        Processes incoming DAP messages, correlating responses with their
        originating requests and forwarding events to handlers.

        Args:
            message: Complete DAP message received from server
        """
        message_type = message.get('type', '')

        if message_type == 'response':
            # Handle response correlation
            request_seq = message.get('request_seq')

            if request_seq is not None and request_seq in self._pending_requests:
                future = self._pending_requests.pop(request_seq)

                if not future.done():
                    future.set_result(message)
                else:
                    self.debug_message(f'Response received for already completed request: {message}')

        elif message_type == 'event':
            # Forward events to event handler
            await self.on_event(message)

        else:
            # Unknown message type
            self.debug_message(f'Unhandled message type: {message}')

    async def request(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a request and wait for the corresponding response.

        Provides synchronous-style request/response communication over async
        transport by correlating requests and responses using sequence numbers.

        Args:
            message: Request message with required DAP fields

        Returns:
            dict: Response message from the server

        Raises:
            RuntimeError: If request is missing required fields or fails
            ConnectionError: If connection fails during request
            asyncio.TimeoutError: If response times out
        """
        # Validate required fields
        if 'command' not in message:
            self.raise_exception(RuntimeError("Request message must include a 'command' field"))

        if 'type' not in message:
            self.raise_exception(RuntimeError("Request message must include a 'type' field"))

        if 'seq' not in message:
            self.raise_exception(RuntimeError("Request message must include a 'seq' field"))

        # Verify connection
        if not self._transport.is_connected():
            self.raise_exception(RuntimeError('Server is not connected'))

        # Get sequence number for correlation
        seq = message['seq']

        # Create future for response correlation
        future = asyncio.Future()
        self._pending_requests[seq] = future

        try:
            # Send request through transport
            await self._send(message)
        except Exception:
            self.raise_exception(ConnectionError('Could not send request'))

        try:
            # Wait for correlated response
            response = await future
            return response

        except (ConnectionError, ConnectionResetError) as e:
            # Connection errors trigger cleanup
            await self.disconnect()
            self.raise_exception(ConnectionError(f'{e}'))

        except asyncio.TimeoutError:
            # Handle timeouts specifically
            self.raise_exception(asyncio.TimeoutError('Connection time out'))

        except Exception as e:
            # Handle other errors
            self.raise_exception(RuntimeError(f'Request failed: {e}'))

        finally:
            # Always clean up the pending request
            self._pending_requests.pop(seq, None)

    async def connect(self) -> None:
        """
        Establish connection to the DAP server.

        Initiates connection through the transport layer and updates
        connection state when successful.

        Raises:
            ConnectionError: If connection fails
            TimeoutError: If connection times out
        """
        # Establish transport connection
        await self._transport.connect()

    async def disconnect(self) -> None:
        """
        Close connection to the DAP server and clean up resources.

        Gracefully closes the transport connection and cleans up any
        remaining connection state or pending operations.
        """
        # Close transport connection
        await self._transport.disconnect()
