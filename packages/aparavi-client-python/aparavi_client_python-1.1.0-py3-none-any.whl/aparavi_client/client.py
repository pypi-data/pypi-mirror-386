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
Aparavi Python Client - Main Interface.

This module provides the primary AparaviClient class for interacting with Aparavi servers.
Use this client to connect to Aparavi services, execute pipelines, chat with AI, and manage data operations.

Basic Usage:
    # Connect and execute a pipeline
    async with AparaviClient(uri="http://localhost:8080", auth="your_api_key") as client:
        token = await client.use(filepath="pipeline.json")
        await client.send(token, "Hello, world!")

    # Chat with AI
    from aparavi_client.schema import Question
    question = Question()
    question.addQuestion("What is machine learning?")
    response = await client.chat(token="chat_token", question=question)
"""

import os
import urllib.parse
from .core import DAPClient, TransportWebSocket, AparaviException, CONST_DEFAULT_SERVICE
from .mixins.connection import ConnectionMixin
from .mixins.execution import ExecutionMixin
from .mixins.data import DataMixin
from .mixins.chat import ChatMixin
from .mixins.events import EventMixin
from .mixins.ping import PingMixin

client_id = 0

__all__ = [
    'AparaviClient',
    'AparaviException',
]


class AparaviClient(
    ConnectionMixin,
    ExecutionMixin,
    DataMixin,
    ChatMixin,
    EventMixin,
    PingMixin,
    DAPClient,
):
    """
    Main Aparavi client for connecting to Aparavi servers and services.

    This client combines all functionality needed to work with Aparavi:
    - Connection management (connect/disconnect)
    - Pipeline execution (start, monitor, terminate pipelines)
    - Data operations (send data, upload files, streaming)
    - AI chat functionality (ask questions, get responses)
    - Event handling (monitor pipeline progress, receive notifications)
    - Server connectivity testing (ping operations)

    The client supports both synchronous and asynchronous usage patterns
    and can be used as a context manager for automatic connection handling.

    Args:
        uri (str): Service URI of the Aparavi server (e.g., "http://localhost:8080").
            If not provided, uses APARAVI_URI environment variable or default service.
        auth (str): Your API key or access token for authentication.
            If not provided, uses APARAVI_APIKEY environment variable. Required.
        **kwargs: Additional configuration options like custom module name

    Raises:
        ValueError: If auth is not provided and APARAVI_APIKEY env var is not set
        ConnectionError: If unable to connect to the specified server

    Example:
        # Async context manager (recommended)
        async with AparaviClient(uri="http://localhost:8080", auth="your_api_key") as client:
            # Client is automatically connected
            token = await client.use(filepath="my_pipeline.json")
            result = await client.send(token, "Process this data")

        # Using environment variables
        # Set APARAVI_URI and APARAVI_APIKEY in environment or .env file
        async with AparaviClient(uri="", auth="") as client:
            # Will use environment variables
            token = await client.use(filepath="my_pipeline.json")

        # Manual connection management
        client = AparaviClient(uri="http://localhost:8080", auth="your_api_key")
        await client.connect()
        try:
            # Your operations here
            pass
        finally:
            await client.disconnect()
    """

    def __init__(
        self,
        uri: str,
        auth: str,
        **kwargs,
    ):
        """
        Create a new Aparavi client instance.

        Args:
            uri: WebSocket URI of your Aparavi server (e.g., "ws://localhost:8080")
            auth: Your API key or access token - get this from your Aparavi dashboard
            **kwargs: Additional options:
                - env: Dictionary of environment variables to use instead of os.environ
                - module: Custom module name for client identification

        Raises:
            ValueError: If URI is empty or not a string
        """
        global client_id

        # Get or load environment variables
        env = kwargs.get('env', None)
        if env is None:
            # If not provided, load from .env file only
            self._env = {}
            
            # Try to load .env file
            try:
                env_path = os.path.join(os.getcwd(), '.env')
                if os.path.exists(env_path):
                    with open(env_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            # Skip comments and empty lines
                            if not line or line.startswith('#'):
                                continue
                            # Parse KEY=VALUE format
                            if '=' in line:
                                key, value = line.split('=', 1)
                                key = key.strip()
                                value = value.strip()
                                # Remove quotes if present
                                if (value.startswith('"') and value.endswith('"')) or \
                                   (value.startswith("'") and value.endswith("'")):
                                    value = value[1:-1]
                                self._env[key] = value
            except Exception:
                # File doesn't exist or can't be read - that's okay
                pass
        else:
            # Use the provided env dictionary
            self._env = dict(env)

        # If we didn't get the URI, look at the env. If not there,
        # use the default
        if not uri:
            uri = self._env.get('APARAVI_URI', CONST_DEFAULT_SERVICE)

        if not auth:
            auth = self._env.get('APARAVI_APIKEY', None)

        if not auth:
            raise ValueError("Authentication key is required. Provide 'auth' parameter, 'env' parameter, or set 'APARAVI_APIKEY' in .env file.")

        # Convert HTTP/HTTPS URI to WS/WSS for WebSocket connections
        parsed_uri = urllib.parse.urlparse(uri)
        ws_scheme = 'wss' if parsed_uri.scheme == 'https' else 'ws'
        ws_uri = parsed_uri._replace(scheme=ws_scheme)

        # Store configuration for connection
        self._uri = f'{ws_uri.geturl()}/task/service'
        self._apikey = auth

        # Initialize chat question counter
        self._next_chat_id = 1

        # Synchronous mode support (advanced usage)
        self._loop = None
        self._thread = None

        # Debug Adapter Protocol integration
        self._dap_attempted = False
        self._dap_send = None

        # Create unique client identifier
        client_name = f'CLIENT-{client_id}'
        client_id += 1

        # Set up WebSocket transport for server communication
        transport = TransportWebSocket(uri=self._uri, auth=auth)

        # Initialize the underlying DAP client with transport
        super().__init__(transport=transport, module=kwargs.get('module', client_name), **kwargs)

    # Context manager support for automatic connection handling
    async def __aenter__(self):
        """
        Enter async context manager - automatically connects to server.

        Returns:
            self: The connected client instance
        """
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Exit async context manager - automatically disconnects from server.
        """
        await self.disconnect()
