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
Aparavi Client SDK.

This package provides a comprehensive Python client for executing Aparavi pipelines,
managing data processing workflows, and interacting with AI services using the
Debug Adapter Protocol (DAP).

The Aparavi Client SDK enables you to:
    - Connect to Aparavi servers and manage connections
    - Execute and control data processing pipelines
    - Upload and stream data to pipelines
    - Chat with AI for document analysis and Q&A
    - Monitor pipeline progress with real-time events
    - Test server connectivity and health

Quick Start:
    from aparavi_client import AparaviClient, Question
    
    # Connect and process data
    async with AparaviClient(auth='your_api_key') as client:
        # Start a pipeline
        result = await client.use(filepath='pipeline.json')
        
        # Send data for processing
        response = await client.send(result['token'], 'your data')
        
        # Chat with AI
        question = Question()
        question.addQuestion('What are the key findings?')
        answer = await client.chat(token=result['token'], question=question)

For more information, see the documentation at https://docs.aparavi.com
"""

__version__ = '1.1.0'
__author__ = 'Aparavi Development Team'
__email__ = 'dev@aparavi.com'

# Import main classes for convenient access
from .schema import (
    Answer,
    Question,
    QuestionExample,
    QuestionHistory,
    QuestionText,
    QuestionType,
    DocFilter,
    DocMetadata,
    Doc,
    DocGroup,
)

from .types import (
    AparaviClientConfig,
    ConnectCallback,
    ConnectionInfo,
    DAPMessage,
    DisconnectCallback,
    EVENT_TYPE,
    EventCallback,
    PipelineComponent,
    PipelineConfig,
    TASK_STATE,
    TASK_STATUS_FLOW,
    TASK_STATUS,
    TraceInfo,
    TransportCallbacks,
)

from .client import AparaviClient, AparaviException

__all__ = [
    'Answer',
    'AparaviClient',
    'AparaviClientConfig',
    'AparaviException',
    'ConnectCallback',
    'ConnectionInfo',
    'DAPMessage',
    'DisconnectCallback',
    'Doc',
    'DocFilter',
    'DocGroup',
    'DocMetadata',
    'EVENT_TYPE',
    'EventCallback',
    'PipelineComponent',
    'PipelineConfig',
    'Question',
    'QuestionExample',
    'QuestionHistory',
    'QuestionText',
    'QuestionType',
    'TASK_STATE',
    'TASK_STATUS_FLOW',
    'TASK_STATUS',
    'TraceInfo',
    'TransportCallbacks',
]
