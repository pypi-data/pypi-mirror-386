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
Pipeline Configuration Types for Aparavi Data Processing.

This module defines types for constructing and configuring Aparavi data processing pipelines.
Pipelines are composed of connected components that process data through transformation,
analysis, routing, and AI operations. Understanding these types is essential for building
custom data processing workflows.

Types Defined:
    PipelineComponent: Individual processing unit within a pipeline
    ComponentInputConnection: Data flow connection between components
    Pipeline: Complete pipeline definition with components and execution parameters
    PipelineConfig: Top-level configuration wrapper for pipeline execution
    UploadResult: File upload progress and result tracking

Pipeline Architecture:
    Pipelines consist of components connected in a directed graph where data flows
    from input connections through processing components to output destinations.
    Each component:
    - Has a unique ID within the pipeline
    - Specifies a provider type (webhook, ai_chat, response, etc.)
    - Contains provider-specific configuration
    - Declares input connections from other components
    - Processes data and passes results to connected components

Data Flow Model:
    Components receive input on named "lanes" and send output to downstream components.
    The ComponentInputConnection type defines these connections:
    - 'from': Source component ID that provides data
    - 'lane': Named output lane from the source component
    
    Example flow:
    webhook (source) --> [lane: 'output'] --> ai_chat --> [lane: 'answer'] --> response

Usage:
    from aparavi_client.types import Pipeline, PipelineComponent, PipelineConfig
    
    # Define a simple pipeline
    pipeline: Pipeline = {
        'project_id': 'my-project',
        'source': 'webhook_input',
        'components': [
            {
                'id': 'webhook_input',
                'provider': 'webhook',
                'config': {'path': '/api/data'}
            },
            {
                'id': 'ai_processor',
                'provider': 'ai_chat',
                'config': {'model': 'gpt-4'},
                'input': [{'from': 'webhook_input', 'lane': 'output'}]
            },
            {
                'id': 'output',
                'provider': 'response',
                'config': {},
                'input': [{'from': 'ai_processor', 'lane': 'answer'}]
            }
        ]
    }
    
    # Use the pipeline
    config: PipelineConfig = {'pipeline': pipeline}
    token = await client.use(config)
"""

from typing import Any, TypedDict, Literal

# Create TypedDict dynamically to avoid keyword conflict
ComponentInputConnection = TypedDict(
    'ComponentInputConnection',
    {
        'lane': str,  # REQUIRED
        'from': str,  # REQUIRED
    },
)


class PipelineComponent(TypedDict, total=False):
    """
    Pipeline component that processes data.

    Note: id, provider, and config are required fields.
    """

    id: str  # Unique identifier for this component within the pipeline - REQUIRED
    provider: str  # Component type/provider (e.g., 'webhook', 'response', 'ai_chat') - REQUIRED
    config: dict[str, Any]  # Component-specific configuration parameters - REQUIRED
    name: str  # Human-readable component name
    description: str  # Component description for documentation
    ui: dict[str, Any]  # UI-specific configuration for visual editors
    input: list[ComponentInputConnection]  # Input connections from other components


class Pipeline(TypedDict):
    """
    Pipeline definition with components and execution parameters.

    All fields are required.
    """

    components: list[PipelineComponent]  # Array of pipeline components that process data - REQUIRED
    source: str  # ID of the component that serves as the pipeline entry point - REQUIRED
    project_id: str  # Project identifier for organization and permissions - REQUIRED


class PipelineConfig(TypedDict):
    """
    Pipeline configuration for Aparavi data processing workflows.

    Defines a complete pipeline with components, data flow connections,
    and execution parameters. Pipelines process data through a series
    of connected components that transform, analyze, or route information.
    """

    pipeline: Pipeline  # REQUIRED


class UploadResult(TypedDict, total=False):
    """
    File upload progress and result information.

    Tracks the progress and outcome of file upload operations,
    providing real-time feedback on transfer status and performance.

    Note: action, filepath, bytes_sent, file_size, and upload_time are required fields.
    """

    action: Literal['open', 'write', 'close', 'complete', 'error']  # Current upload action or final status - REQUIRED
    filepath: str  # Name/path of the file being uploaded - REQUIRED
    bytes_sent: int  # Number of bytes successfully transmitted - REQUIRED
    file_size: int  # Total size of the file in bytes - REQUIRED
    upload_time: float  # Time elapsed for the upload operation in seconds - REQUIRED
    result: dict[str, Any]  # Server response data for completed uploads
    error: str  # Error message if upload failed
