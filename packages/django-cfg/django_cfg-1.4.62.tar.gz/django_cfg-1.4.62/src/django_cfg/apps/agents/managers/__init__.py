"""
Django Agents - Custom model managers.
"""

from .execution import AgentExecutionManager, WorkflowExecutionManager
from .registry import AgentDefinitionManager, AgentTemplateManager
from .toolsets import (
    ApprovalLogManager,
    ToolExecutionManager,
    ToolPermissionManager,
    ToolsetConfigurationManager,
)

__all__ = [
    # Execution managers
    'AgentExecutionManager',
    'WorkflowExecutionManager',

    # Registry managers
    'AgentDefinitionManager',
    'AgentTemplateManager',

    # Toolsets managers
    'ToolExecutionManager',
    'ApprovalLogManager',
    'ToolsetConfigurationManager',
    'ToolPermissionManager',
]
