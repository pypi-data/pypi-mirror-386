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
Core Constants for Aparavi Client.

This module defines global constants used throughout the Aparavi client library.
These constants provide default values, timeouts, and service endpoints that
ensure consistent behavior across all client operations.

Constants:
    CONST_DEFAULT_SERVICE: Default Aparavi service URI. This is used when no
                          custom service URI is provided during client initialization.
                          Points to the official Aparavi Enterprise as a Service (EaaS)
                          endpoint.
    
    CONST_SOCKET_TIMEOUT: WebSocket timeout in seconds. This value controls how long
                         the client will wait for server responses before timing out.
                         Set to 180 seconds (3 minutes) to accommodate long-running
                         operations while still detecting dead connections.

Usage:
    from aparavi_client.core.constants import CONST_DEFAULT_SERVICE, CONST_SOCKET_TIMEOUT
    
    # Use default service endpoint
    client = AparaviClient(uri=CONST_DEFAULT_SERVICE, auth='api_key')
    
    # Access timeout for custom configurations
    custom_timeout = CONST_SOCKET_TIMEOUT * 2  # Double the default timeout
"""

# Default Aparavi service endpoint
# This points to the production Enterprise as a Service (EaaS) instance
CONST_DEFAULT_SERVICE = 'https://eaas.aparavi.com'

# WebSocket timeout in seconds
# This controls how long to wait for server responses before timing out
# Set to 3 minutes to handle long-running operations like large file uploads
# or complex pipeline processing while still detecting connection failures
CONST_SOCKET_TIMEOUT = 180
