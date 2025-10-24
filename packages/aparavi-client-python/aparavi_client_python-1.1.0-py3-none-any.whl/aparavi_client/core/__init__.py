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
Core Components for Aparavi Client.

This module provides the foundational components that power the Aparavi client:
    - DAP (Debug Adapter Protocol) base classes and client implementation
    - WebSocket transport layer for server communication
    - Exception classes for structured error handling
    - Core constants and configuration values

These components are used internally by the AparaviClient and typically don't need
to be imported directly unless you're extending the client or implementing custom
transport layers.

Components:
    DAPBase: Base class providing DAP messaging and logging capabilities
    DAPClient: Client implementation of the Debug Adapter Protocol
    TransportBase: Abstract base class for transport implementations  
    TransportWebSocket: WebSocket transport for client-server communication
    AparaviException: Base exception class for all Aparavi operations
    ConnectionException: Raised for connection-related errors
    PipeException: Raised for data pipe operation errors
    ExecutionException: Raised for pipeline execution errors
    ValidationException: Raised for input validation failures

Usage:
    # These are typically used internally, but can be imported for advanced use cases
    from aparavi_client.core import DAPClient, TransportWebSocket, AparaviException
"""

from .dap_base import DAPBase
from .dap_client import DAPClient
from .transport_websocket import TransportWebSocket
from .transport import TransportBase
from .constants import CONST_DEFAULT_SERVICE, CONST_SOCKET_TIMEOUT
from .exceptions import (
    DAPException,
    AparaviException,
    ConnectionException,
    PipeException,
    ExecutionException,
    ValidationException,
)

__all__ = [
    'CONST_DEFAULT_SERVICE',
    'CONST_SOCKET_TIMEOUT',
    'AparaviException',
    'ConnectionException',
    'PipeException',
    'ExecutionException',
    'ValidationException',
    'DAPBase',
    'DAPClient',
    'DAPException',
    'TransportBase',
    'TransportWebSocket',
]
