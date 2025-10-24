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
Custom Exception Classes for Aparavi Operations.

This module provides specialized exception classes for different types of errors
that can occur when working with Aparavi. These exceptions provide better error
context and make it easier to handle different failure scenarios appropriately.

The exception hierarchy helps you:
- Distinguish between different types of failures
- Access detailed error information from the server
- Handle errors at the appropriate level of specificity
- Debug issues with comprehensive error context

Usage:
    from aparavi.exceptions import ConnectionException, PipeException

    try:
        await client.connect()
        result = await client.send(token, data)
    except ConnectionException as e:
        print(f"Connection failed: {e}")
        # Handle connection-specific errors
    except PipeException as e:
        print(f"Data pipe error: {e}")
        # Handle data transfer errors
    except AparaviException as e:
        print(f"General Aparavi error: {e}")
        # Handle any other Aparavi errors
"""

from typing import Any, Dict


class DAPException(Exception):
    """
    Base exception class for Debug Adapter Protocol (DAP) errors.

    This exception wraps DAP error responses to provide structured access to
    error information including file locations, line numbers, and other
    contextual data returned by Aparavi servers.

    The class preserves the complete DAP result dictionary while extracting
    the error message for standard exception handling patterns.

    Attributes:
        dap_result: Complete DAP result dictionary containing detailed error
                   information and context from the server

    Example:
        try:
            result = await client.some_operation()
            if client.did_fail(result):
                raise DAPException(result)
        except DAPException as e:
            print(f"Error: {e}")

            # Access detailed error context
            if 'file' in e.dap_result and 'line' in e.dap_result:
                print(f"Location: {e.dap_result['file']}:{e.dap_result['line']}")

            # Access full error context
            print(f"Full details: {e.dap_result}")
    """

    def __init__(self, dap_result: Dict[str, Any]):
        """
        Initialize DAPException with a DAP result dictionary.

        Args:
            dap_result: DAP response dictionary containing error information.
                       Expected to have a 'message' field with the error description,
                       and may include additional context like 'file', 'line', etc.
        """
        # Extract error message for the base exception
        error_message = dap_result.get('message', 'Unknown DAP error')
        super().__init__(error_message)

        # Store complete DAP result for detailed error analysis
        self.__dap_results__ = dap_result or {}


class AparaviException(DAPException):
    """
    Base exception for all Aparavi operations.

    This is the root exception class for all Aparavi-specific errors.
    Catch this exception type to handle any error that originates from
    Aparavi operations while still having access to detailed error context.

    Example:
        try:
            async with AparaviClient(uri, auth) as client:
                result = await client.use(filepath="pipeline.json")
                await client.send(result['token'], data)
        except AparaviException as e:
            print(f"Aparavi operation failed: {e}")
            # This catches all Aparavi-specific errors
        except Exception as e:
            print(f"Unexpected error: {e}")
            # This catches non-Aparavi errors
    """

    pass


class ConnectionException(AparaviException):
    """
    Exception raised for connection-related issues.

    Raised when there are problems connecting to Aparavi servers,
    maintaining connections, or when connections are lost unexpectedly.

    Common scenarios:
    - Server is unreachable or offline
    - Network connectivity issues
    - Authentication failures
    - WebSocket connection problems
    - Connection timeouts

    Example:
        try:
            await client.connect()
        except ConnectionException as e:
            print(f"Failed to connect to Aparavi server: {e}")
            # Maybe retry with different settings or show user error
        except Exception as e:
            print(f"Unexpected connection error: {e}")
    """

    pass


class PipeException(AparaviException):
    """
    Exception raised for data pipe operations.

    Raised when there are problems with data pipes used for sending
    data to pipelines, uploading files, or streaming operations.

    Common scenarios:
    - Failed to open data pipe
    - Error writing data to pipe
    - Pipe closed unexpectedly
    - Data format or size issues
    - Server-side processing errors

    Example:
        try:
            pipe = await client.pipe(token, mimetype="text/csv")
            await pipe.open()
            await pipe.write(csv_data)
            result = await pipe.close()
        except PipeException as e:
            print(f"Data pipe error: {e}")
            # Handle data transfer failures
        except Exception as e:
            print(f"Unexpected pipe error: {e}")
    """

    pass


class ExecutionException(AparaviException):
    """
    Exception raised for pipeline execution issues.

    Raised when there are problems starting, running, or managing
    Aparavi pipelines and processing tasks.

    Common scenarios:
    - Pipeline configuration errors
    - Failed to start pipeline
    - Pipeline crashed during execution
    - Resource allocation problems
    - Invalid pipeline parameters

    Example:
        try:
            result = await client.use(filepath="broken_pipeline.json")
            token = result['token']
        except ExecutionException as e:
            print(f"Pipeline execution failed: {e}")
            # Check pipeline configuration or server resources
        except Exception as e:
            print(f"Unexpected execution error: {e}")
    """

    pass


class ValidationException(AparaviException):
    """
    Exception raised for input validation failures.

    Raised when input data, configurations, or parameters don't meet
    the requirements for Aparavi operations.

    Common scenarios:
    - Invalid file paths or missing files
    - Malformed configuration data
    - Invalid API keys or tokens
    - Unsupported data formats
    - Parameter value out of range

    Example:
        try:
            # This might raise ValidationException if file doesn't exist
            result = await client.use(filepath="nonexistent.json")
        except ValidationException as e:
            print(f"Input validation failed: {e}")
            # Check your inputs and fix the issue
        except Exception as e:
            print(f"Unexpected validation error: {e}")
    """

    pass
