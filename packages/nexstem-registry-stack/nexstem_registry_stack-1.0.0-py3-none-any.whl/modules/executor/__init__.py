"""
Executor module.

This module provides the main Executor class and all related types
for managing pipeline execution in the SW Registry Stack.
"""

from .executor import Executor
from .dto import (
    ExecutorConfig,
    ExecutorCreateOptions,
    ExecutorListOptions,
    ExecutorHistoryOptions,
    ExecutorInfoOptions,
    ExecutorStartOptions,
    ExecutorStopOptions,
    ExecutorDestroyOptions,
    ExecutorVersionOptions,
    PipelineCreateResponse,
    PipelineCreateData,
    PipelineListResponse,
    PipelineListData,
    PipelineHistoryResponse,
    PipelineHistoryData,
    PipelineInfoResponse,
    PipelineStateTransitionResponse,
    PipelineStateTransitionData,
    ExecutorVersionResponse,
    ExecutorVersionData
)

__all__ = [
    'Executor',
    'ExecutorConfig',
    'ExecutorCreateOptions',
    'ExecutorListOptions',
    'ExecutorHistoryOptions',
    'ExecutorInfoOptions',
    'ExecutorStartOptions',
    'ExecutorStopOptions',
    'ExecutorDestroyOptions',
    'ExecutorVersionOptions',
    'PipelineCreateResponse',
    'PipelineCreateData',
    'PipelineListResponse',
    'PipelineListData',
    'PipelineHistoryResponse',
    'PipelineHistoryData',
    'PipelineInfoResponse',
    'PipelineStateTransitionResponse',
    'PipelineStateTransitionData',
    'ExecutorVersionResponse',
    'ExecutorVersionData'
]