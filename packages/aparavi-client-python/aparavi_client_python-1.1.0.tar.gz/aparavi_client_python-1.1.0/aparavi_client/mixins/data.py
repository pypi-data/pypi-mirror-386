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
Data Operations and File Upload for Aparavi Client.

This module provides data handling capabilities including sending text data,
uploading files, and streaming data to Aparavi pipelines. Use these functions
to feed data into your pipelines for processing, analysis, and AI operations.

Key Features:
- Send text or binary data to running pipelines
- Upload files with progress tracking and parallel transfers
- Stream data using pipes for large datasets
- Support for various file formats and MIME types
- Automatic retry and error handling

Usage:
    # Send simple text data
    token = await client.use(filepath="text_processor.json")
    result = await client.send(token, "Process this text")

    # Upload multiple files
    files = ["document1.pdf", "data.csv", "image.png"]
    results = await client.send_files(files, token)

    # Stream large dataset
    pipe = await client.pipe(token, mimetype="text/csv")
    await pipe.open()
    await pipe.write(csv_chunk1)
    await pipe.write(csv_chunk2)
    final_result = await pipe.close()
"""

import os
import time
import asyncio
import mimetypes
from pathlib import Path
from typing import Dict, Any, List, Union, Tuple, Optional
from ..core import DAPClient
from ..types import PIPELINE_RESULT, UPLOAD_RESULT


class DataMixin(DAPClient):
    """
    Provides data operations for the Aparavi client.

    This mixin adds the ability to send data to running pipelines, upload files,
    and stream large datasets. It handles both simple data sending and complex
    multi-file uploads with progress tracking.

    Data operations work with pipeline tokens - you first start a pipeline with
    client.use(), then send data to it using the methods in this class.

    Key Capabilities:
    - Send text or binary data to pipelines
    - Upload single or multiple files with progress tracking
    - Stream data using pipes for large datasets
    - Automatic file type detection and MIME type handling
    - Parallel file transfers for better performance
    - Progress events for monitoring uploads

    This is automatically included when you use AparaviClient, so you can
    call methods like client.send() and client.send_files() directly.
    """

    class DataPipe:
        """
        Streaming data pipe for sending large datasets to Aparavi pipelines.

        Use DataPipe when you need to send data in multiple chunks, stream
        large files, or have real-time data feeding requirements. Pipes provide
        more control than the simple send() method.

        The pipe works by:
        1. Opening a connection to the pipeline
        2. Writing data in chunks as needed
        3. Closing the pipe to get final results

        Example:
            # Stream CSV data in chunks
            pipe = await client.pipe(token, mimetype="text/csv")
            async with pipe:  # Automatically opens and closes
                for chunk in csv_chunks:
                    await pipe.write(chunk.encode())
            # Results available after pipe closes
        """

        def __init__(self, client, token: str, objinfo: Dict[str, Any] = None, mime_type: str = None, provider: str = None):
            """
            Create a new data pipe (usually called via client.pipe()).

            Args:
                client: The Aparavi client instance
                token: Pipeline token for data destination
                objinfo: Optional metadata about the data
                mime_type: MIME type of data (e.g., "text/csv", "application/json")
                provider: Optional provider specification
            """
            self._client = client
            self._token = token
            self._objinfo = objinfo or {}
            self._mime_type = mime_type or 'application/octet-stream'
            self._provider = provider
            self._pipe_id = None
            self._opened = False
            self._closed = False

        @property
        def is_opened(self) -> bool:
            """Check if the pipe is currently open for writing."""
            return self._opened

        @property
        def pipe_id(self) -> Optional[int]:
            """Get the unique ID assigned to this pipe by the server."""
            return self._pipe_id

        async def open(self) -> 'DataMixin.DataPipe':
            """
            Open the pipe for data transmission.

            Must be called before writing data. The server assigns a unique
            pipe ID and prepares to receive your data.

            Returns:
                self: The opened pipe instance for method chaining

            Raises:
                RuntimeError: If pipe is already opened or if opening fails

            Example:
                pipe = await client.pipe(token, mimetype="text/plain")
                await pipe.open()
                # Now ready to write data
            """
            if self._opened:
                raise RuntimeError('Pipe already opened')

            request = self._client.build_request(
                'apaext_process',
                arguments={
                    'subcommand': 'open',
                    'object': self._objinfo,
                    'mimeType': self._mime_type,
                    'provider': self._provider,
                },
                token=self._token,
            )

            response = await self._client.request(request)

            if self._client.did_fail(response):
                raise RuntimeError(response.get('message', 'Your pipeline is not currently running.'))

            self._pipe_id = response.get('body', {}).get('pipe_id')
            self._opened = True
            return self

        async def write(self, buffer: bytes) -> None:
            """
            Write data to the pipe.

            Can be called multiple times to send data in chunks. Data must
            be bytes - convert strings using .encode() first.

            Args:
                buffer: Data to send (must be bytes, not string)

            Raises:
                RuntimeError: If pipe not opened or write fails
                ValueError: If buffer is not bytes

            Example:
                await pipe.write(b"First chunk of data")
                await pipe.write("Second chunk".encode())
                await pipe.write(json.dumps(data).encode())
            """
            if not self._opened:
                raise RuntimeError('Pipe not opened')

            if not isinstance(buffer, bytes):
                raise ValueError('Buffer must be bytes')

            request = self._client.build_request(
                'apaext_process',
                arguments={
                    'subcommand': 'write',
                    'pipe_id': self._pipe_id,
                    'data': buffer,
                },
                token=self._token,
            )

            response = await self._client.request(request)

            if self._client.did_fail(response):
                raise RuntimeError(response.get('message', 'Failed to write to pipe'))

        async def close(self) -> PIPELINE_RESULT:
            """
            Close the pipe and get the processing results.

            Must be called after finishing data transmission to signal
            completion and retrieve the pipeline's output.

            Returns:
                Dict: Results from processing the data you sent

            Example:
                pipe = await client.pipe(token, mimetype="text/csv")
                await pipe.open()
                await pipe.write(csv_data.encode())
                results = await pipe.close()
                print(f"Processed {results['records_count']} records")
            """
            if not self._opened or self._closed:
                return {}

            try:
                request = self._client.build_request(
                    'apaext_process',
                    arguments={
                        'subcommand': 'close',
                        'pipe_id': self._pipe_id,
                    },
                    token=self._token,
                )

                response = await self._client.request(request)

                if self._client.did_fail(response):
                    raise RuntimeError(response.get('message', 'Failed to close pipe'))

                return response.get('body', {})

            finally:
                self._closed = True

        async def __aenter__(self):
            """Enter async context manager - automatically opens pipe."""
            return await self.open()

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            """Exit async context manager - automatically closes pipe."""
            await self.close()

    def __init__(self, **kwargs):
        """Initialize data operations."""
        super().__init__(**kwargs)

    async def pipe(self, token: str, objinfo: Dict[str, Any] = None, mime_type: str = None, provider: str = None) -> DataPipe:
        r"""
        Create a data pipe for streaming operations.

        Use pipes when you need to send data in multiple chunks, stream large
        files, or have real-time data feeding requirements. Pipes give you more
        control than the simple send() method.

        Args:
            token: Pipeline token to send data to
            objinfo: Optional metadata about your data (e.g., {"name": "my_data.csv"})
            mime_type: MIME type of your data (auto-detected if not provided)
            provider: Optional provider specification

        Returns:
            DataPipe: A pipe object for streaming data

        Example:
            # Basic pipe usage
            pipe = await client.pipe(token, mime_type="text/csv")
            await pipe.open()
            await pipe.write(csv_header.encode())
            for row in csv_rows:
                await pipe.write(f"{row}\n".encode())
            results = await pipe.close()

            # Using context manager (recommended)
            async with await client.pipe(token, mime_type="application/json") as pipe:
                await pipe.write(json.dumps(data1).encode())
                await pipe.write(json.dumps(data2).encode())
                results = await pipe.close()
            # Results available after context exits
        """
        return self.DataPipe(self, token=token, objinfo=objinfo, mime_type=mime_type, provider=provider)

    async def send(
        self,
        token: str,
        data: Union[str, bytes],
        objinfo: Dict[str, Any] = None,
        mimetype: str = None,
    ) -> PIPELINE_RESULT:
        """
        Send data to a running pipeline.

        This is the simple way to send data when you have all the data ready
        at once. For streaming or multiple chunks, use pipe() instead.

        The data is sent to the pipeline specified by the token, processed
        according to the pipeline's configuration, and results are returned.

        Args:
            token: Pipeline token (from client.use()) to send data to
            data: Your data as string or bytes to process
            objinfo: Optional metadata about the data (e.g., {"name": "data.txt"})
            mimetype: MIME type of the data (auto-detected if not specified)

        Returns:
            Dict: Results from processing your data

        Raises:
            ValueError: If data is not string or bytes
            RuntimeError: If sending fails

        Example:
            # Send text data
            token = await client.use(filepath="text_analyzer.json")
            result = await client.send(token, "Analyze this text for sentiment")
            print(f"Sentiment: {result['sentiment']}")

            # Send JSON data
            import json
            data = {"name": "John", "age": 30}
            result = await client.send(
                token,
                json.dumps(data),
                mimetype="application/json"
            )

            # Send binary data
            with open("data.bin", "rb") as f:
                binary_data = f.read()
            result = await client.send(token, binary_data, mimetype="application/octet-stream")
        """
        # Convert string to bytes if needed
        if isinstance(data, str):
            buffer = data.encode('utf-8')
        elif isinstance(data, bytes):
            buffer = data
        else:
            raise ValueError('data must be either a string or bytes')

        # Create and use a temporary pipe for the data
        pipe = await self.pipe(token, objinfo, mimetype)

        try:
            await pipe.open()
            await pipe.write(buffer)
            return await pipe.close()

        except Exception:
            # Clean up pipe on any error
            if pipe.is_opened:
                try:
                    await pipe.close()
                except Exception:
                    pass  # Ignore cleanup errors
            raise

    async def send_files(
        self,
        files: List[
            Union[
                str,
                Tuple[str, Optional[Dict[str, Any]]],
                Tuple[str, Optional[Dict[str, Any]], Optional[str]],
            ]
        ],
        token: str,
    ) -> UPLOAD_RESULT:
        """
        Upload multiple files to a pipeline with progress tracking.

        Efficiently uploads files using parallel transfers with automatic
        progress events. Files are processed concurrently for better performance.

        Each file can be specified as:
        - Just a file path: "/path/to/file.pdf"
        - File path with metadata: ("/path/to/file.pdf", {"category": "document"})
        - File path with metadata and MIME type: ("/path/to/file.pdf", {"name": "doc"}, "application/pdf")

        Args:
            files: List of files to upload (see formats above)
            token: Pipeline token to upload files to

        Returns:
            List[Dict]: Upload results for each file with status, timing, and processing results

        Raises:
            ValueError: If files list is empty, file paths invalid, or token missing
            FileNotFoundError: If any specified file doesn't exist
            RuntimeError: If API key is not configured

        Example:
            # Simple file upload
            files = [
                "document1.pdf",
                "data.csv",
                "report.docx"
            ]
            results = await client.send_files(files, token)

            for result in results:
                if result['action'] == 'complete':
                    print(f"✓ Uploaded {result['filepath']} in {result['upload_time']:.2f}s")
                else:
                    print(f"✗ Failed {result['filepath']}: {result['error']}")

            # Upload with metadata
            files = [
                ("financial_report.pdf", {"department": "finance", "year": 2024}),
                ("sales_data.csv", {"type": "quarterly_data"}, "text/csv")
            ]
            results = await client.send_files(files, token)

        Progress Events:
            If you've configured event handling, you'll receive progress events:
            - 'open': File upload starting
            - 'write': Data being transferred (with bytes sent/total)
            - 'close': File upload completing
            - 'complete': File successfully processed
            - 'error': Upload or processing failed

        Tips for Large Uploads:
            - Use specific MIME types for better processing
            - Add descriptive metadata to help with organization
            - Monitor progress events for user feedback
            - Files are uploaded in parallel (up to the number of threads you specified when starting your pipeline with threads option)
        """
        # Fixed chunk size for optimal performance
        chunk_size = 1024 * 1024  # 1MB

        # Maximum concurrent uploads
        MAX_WORKERS = 64

        # Validate inputs
        if not files:
            raise ValueError('Files list cannot be empty')

        if not token or not isinstance(token, str):
            raise ValueError('Token must be a non-empty string')

        if not self._apikey:
            raise RuntimeError('API key is required for file uploads')

        # Normalize file entries to (filepath, objinfo, mimetype) tuples
        normalized_files = []
        for entry in files:
            if isinstance(entry, str):
                # Just filepath - auto-detect MIME type and use filename
                filepath = entry
                filename = Path(filepath).name
                objinfo = {'name': filename}
                mimetype = mimetypes.guess_type(filepath)[0] or 'application/octet-stream'
            elif isinstance(entry, tuple):
                if len(entry) == 2:
                    # (filepath, objinfo)
                    filepath, objinfo = entry
                    if objinfo is None:
                        filename = Path(filepath).name
                        objinfo = {'name': filename}
                    mimetype = mimetypes.guess_type(filepath)[0] or 'application/octet-stream'
                elif len(entry) == 3:
                    # (filepath, objinfo, mimetype)
                    filepath, objinfo, mimetype = entry
                    if objinfo is None:
                        filename = Path(filepath).name
                        objinfo = {'name': filename}
                    if mimetype is None:
                        mimetype = mimetypes.guess_type(filepath)[0] or 'application/octet-stream'
                else:
                    raise ValueError(f'Invalid tuple length for entry: {entry}')
            else:
                raise ValueError(f'Invalid file entry type: {type(entry)}')

            # Validate file exists
            if not os.path.isfile(filepath):
                raise ValueError(f'File not found: {filepath}')

            normalized_files.append((filepath, objinfo, mimetype))

        # Set up concurrent upload processing
        task_queue = asyncio.Queue()
        results = [None] * len(normalized_files)
        pending_exception = None

        # Populate queue with file upload tasks
        for index, (filepath, objinfo, mimetype) in enumerate(normalized_files):
            await task_queue.put((index, filepath, objinfo, mimetype))

        async def send_upload_event(body: Dict[str, Any]) -> None:
            """Send upload progress event through the event system."""
            nonlocal pending_exception

            try:
                event_message = {
                    'event': 'apaevt_status_upload',
                    'body': body,
                    'seq': 0,
                    'type': 'event',
                }

                if self._caller_on_event:
                    await self._caller_on_event(event_message)

            except Exception as e:
                pending_exception = e

        async def worker_task() -> None:
            """Worker task that processes file uploads from the queue."""
            current_task = asyncio.current_task()
            worker_name = current_task.get_name() if current_task else 'worker'

            while not task_queue.empty():
                try:
                    # Get next file to upload
                    try:
                        index, filepath, objinfo, mimetype = task_queue.get_nowait()
                    except asyncio.QueueEmpty:
                        break

                    if pending_exception:
                        break

                    start_time = time.time()
                    bytes_sent = 0
                    pipe = None
                    file_exception = None
                    close_result = None

                    try:
                        # Get file size for progress tracking
                        file_size = os.path.getsize(filepath)

                        # Add file size to metadata
                        if 'size' not in objinfo:
                            objinfo = dict(objinfo)
                            objinfo['size'] = file_size

                        # Create and open upload pipe
                        pipe = await self.pipe(token, objinfo, mimetype)
                        self.debug_message(f'[{worker_name}] Opening pipe for {filepath}')
                        await pipe.open()
                        self.debug_message(f'[{worker_name}] Pipe {pipe.pipe_id} opened for {filepath}')

                        # Send upload start event
                        await send_upload_event(
                            {
                                'action': 'open',
                                'filepath': filepath,
                                'file_size': file_size,
                            }
                        )

                        # Upload file in chunks
                        with open(filepath, 'rb') as f:
                            while True:
                                if pending_exception:
                                    file_exception = pending_exception
                                    break

                                chunk = f.read(chunk_size)
                                if not chunk:
                                    break

                                await pipe.write(chunk)
                                bytes_sent += len(chunk)

                                # Send progress event
                                await send_upload_event(
                                    {
                                        'action': 'write',
                                        'filepath': filepath,
                                        'bytes_sent': bytes_sent,
                                        'file_size': file_size,
                                    }
                                )

                    except Exception as e:
                        file_exception = e
                        self.debug_message(f'[{worker_name}] Error during transfer for {filepath}: {e}')

                    # Always try to close the pipe
                    if pipe and pipe.is_opened:
                        try:
                            if not file_exception:
                                await send_upload_event(
                                    {
                                        'action': 'close',
                                        'filepath': filepath,
                                        'bytes_sent': bytes_sent,
                                        'file_size': file_size,
                                    }
                                )

                            close_result = await pipe.close()
                            self.debug_message(f'[{worker_name}] Pipe {pipe.pipe_id} closed for {filepath}')

                        except Exception as e:
                            if not file_exception:
                                file_exception = e
                            self.debug_message(f'[{worker_name}] Error closing pipe for {filepath}: {e}')

                    # Calculate upload time
                    upload_time = time.time() - start_time

                    # Create result event
                    event_body = {
                        'action': 'complete' if file_exception is None else 'error',
                        'filepath': filepath,
                        'bytes_sent': bytes_sent,
                        'file_size': file_size,
                        'upload_time': upload_time,
                        'result': close_result,
                    }

                    if file_exception is not None:
                        event_body['error'] = str(file_exception)

                    # Send final status event
                    try:
                        await send_upload_event(event_body)
                    except Exception:
                        pass

                    # Store result
                    results[index] = event_body

                    # Log completion
                    if file_exception:
                        self.debug_message(f'[{worker_name}] Upload failed: {filepath} ({bytes_sent}/{file_size} bytes): {file_exception}')
                    else:
                        self.debug_message(f'[{worker_name}] Upload completed: {filepath} ({bytes_sent} bytes, {upload_time:.2f}s)')

                    task_queue.task_done()

                except Exception as worker_error:
                    self.debug_message(f'[{worker_name}] Worker error: {worker_error}')
                    try:
                        task_queue.task_done()
                    except ValueError:
                        pass

        # Start upload processing
        self.debug_message(f'Starting queue-based upload of {len(normalized_files)} files with {MAX_WORKERS} workers (token={token})')

        try:
            # Create and start worker tasks
            num_workers = min(MAX_WORKERS, len(normalized_files))

            worker_tasks = []
            for i in range(num_workers):
                task = asyncio.create_task(worker_task(), name=f'upload-worker-{i + 1}')
                worker_tasks.append(task)

            # Wait for all workers to complete
            await asyncio.gather(*worker_tasks)

        except KeyboardInterrupt:
            self.debug_message('Upload interrupted by user - allowing workers to finish current files')
            await asyncio.gather(*worker_tasks, return_exceptions=True)

        except Exception as e:
            self.debug_message(f'Upload process failed: {e}')
            await asyncio.gather(*worker_tasks, return_exceptions=True)

        # Fill in any missing results
        for i, result in enumerate(results):
            if result is None:
                filepath = normalized_files[i][0]
                results[i] = {
                    'action': 'error',
                    'filepath': filepath,
                    'bytes_sent': 0,
                    'file_size': 0,
                    'upload_time': 0,
                    'error': 'Upload not processed',
                    'result': None,
                }

        # Log summary
        successful_uploads = sum(1 for r in results if r and r.get('action') == 'complete')
        failed_uploads = len(results) - successful_uploads
        total_bytes = sum(r.get('bytes_sent', 0) for r in results if r and r.get('action') == 'complete')

        self.debug_message(f'Queue-based upload completed: {successful_uploads} successful, {failed_uploads} failed, {total_bytes} total bytes transferred (token={token})')

        return results
