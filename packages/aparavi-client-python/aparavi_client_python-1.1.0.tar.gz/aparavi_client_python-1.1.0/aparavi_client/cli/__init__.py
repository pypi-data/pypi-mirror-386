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
Command Line Interface for Aparavi Client.

This package provides a comprehensive CLI for interacting with Aparavi services
from the command line. The CLI offers commands for pipeline execution, file uploads,
status monitoring, and event tracking with rich terminal UI.

Commands:
    start: Start and execute Aparavi pipelines
    upload: Upload files to running pipelines
    status: Monitor pipeline execution status
    stop: Terminate running pipelines
    events: Stream real-time events from pipelines

The CLI provides a user-friendly terminal interface with:
    - Progress bars for uploads
    - Real-time status updates
    - Color-coded output
    - Interactive monitoring
    - Error reporting with context

Usage:
    # From command line
    aparavi start --pipeline my_pipeline.json --apikey YOUR_KEY
    aparavi upload --files *.pdf --token PIPELINE_TOKEN
    aparavi status --token PIPELINE_TOKEN
    
For detailed help:
    aparavi --help
    aparavi start --help
"""
