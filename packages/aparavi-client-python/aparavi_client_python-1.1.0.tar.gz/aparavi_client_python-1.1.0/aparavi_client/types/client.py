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
Client Type Definitions for Aparavi Client.

This module provides TypedDict classes and type aliases for type-safe client configuration,
DAP (Debug Adapter Protocol) messages, and callback signatures. These types improve code
completion, enable static type checking, and document expected data structures.

Types Defined:
    DAPMessage: Core message structure for client-server communication
    TransportCallbacks: Callback hooks for transport layer events
    ConnectionInfo: Connection configuration for server endpoints
    AparaviClientConfig: Complete client configuration options
    EventCallback: Type alias for event handling callbacks
    ConnectCallback: Type alias for connection callbacks
    DisconnectCallback: Type alias for disconnection callbacks
    TraceInfo: Stack trace information for debugging errors

These types are compatible with Python 3.8+ using native typing without extensions.

Usage:
    from aparavi_client.types import AparaviClientConfig, EventCallback
    
    # Type-safe configuration
    config: AparaviClientConfig = {
        'auth': 'your_api_key',
        'uri': 'wss://server.example.com',
        'onEvent': my_event_handler
    }
    
    # Type hints for callbacks
    async def handle_event(event: DAPMessage) -> None:
        print(f"Event: {event['event']}")
"""

from typing import Any, Callable, Awaitable, TypedDict, Literal, Optional


class TraceInfo(TypedDict):
    """Stack trace information for errors."""

    file: str
    lineno: int


class DAPMessage(TypedDict, total=False):
    """
    Core message structure for Debug Adapter Protocol (DAP) communication.

    Used for all client-server communication including requests, responses,
    and events. Supports both text and binary data transmission through
    the DAP protocol format.

    Note: Using total=False makes all fields optional by default.
    Required fields are documented in comments.
    """

    # Required fields (must be present in all messages)
    type: Literal['request', 'response', 'event']  # REQUIRED
    seq: int  # REQUIRED

    # Optional fields
    command: str  # Command name for requests (e.g., 'execute', 'terminate', 'apaext_ping')
    arguments: dict[str, Any]  # Command arguments and parameters
    body: dict[str, Any]  # Response body containing results and data
    success: bool  # Success flag for responses - true if operation succeeded
    message: str  # Error or status message
    request_seq: int  # Sequence number of the request this response corresponds to
    event: str  # Event type name for event messages
    token: str  # Task or pipeline token for operation context
    data: bytes | str  # Binary or text data payload
    trace: TraceInfo  # Stack trace information for errors


class TransportCallbacks(TypedDict, total=False):
    """
    Callback functions for transport layer events and debugging.

    These callbacks provide hooks for monitoring transport activity,
    debugging protocol messages, and handling connection lifecycle events.
    """

    onDebugMessage: Callable[[str], None]  # Called when debug messages are generated
    onDebugProtocol: Callable[[str], None]  # Called when protocol messages are sent/received for debugging
    onReceive: Callable[[DAPMessage], Awaitable[None]]  # Called when a message is received from the server
    onConnected: Callable[[Optional[str]], Awaitable[None]]  # Called when connection is established
    onDisconnected: Callable[[Optional[str], Optional[bool]], Awaitable[None]]  # Called when connection is lost or closed


class ConnectionInfo(TypedDict):
    """
    Connection configuration for establishing server connections.

    Note: uri is required, auth is optional.
    """

    uri: str  # Server URI (WebSocket endpoint) - REQUIRED
    auth: Optional[str]  # Authentication token or API key - OPTIONAL


# Type aliases for callback functions
"""
Callback function for handling real-time events from the server.

Events include pipeline status updates, processing progress,
error notifications, and system alerts.
"""
EventCallback = Callable[[DAPMessage], Awaitable[None]]

"""Callback function for connection establishment events."""
ConnectCallback = Callable[[Optional[str]], Awaitable[None]]

"""Callback function for disconnection events."""
DisconnectCallback = Callable[[Optional[str], Optional[bool]], Awaitable[None]]


class AparaviClientConfig(TypedDict, total=False):
    """
    Configuration options for creating an AparaviClient instance.

    Provides connection settings, authentication, and event handling
    configuration for establishing and managing server connections.

    All fields are optional.
    """

    # Required fields
    auth: str  # API authentication key or token

    # Optional fields
    uri: str  # Server URI (will be converted to WebSocket URI automatically)
    onEvent: EventCallback  # Callback for handling real-time events from server
    onConnected: ConnectCallback  # Callback for connection establishment
    onDisconnected: DisconnectCallback  # Callback for disconnection events
    module: str  # Client module name for debugging and identification
