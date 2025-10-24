# Copyright (C) 2025 Yassine Bargach
# Licensed under the GNU Affero General Public License v3
# See LICENSE file for full license information.

"""Core framework for automated security research and web application testing.

This module provides the main framework components including configuration
management, database initialization, sandbox setup, and model registry
for the security research CLI application.
"""

from .config.settings import Config
from .core import config_setup, init_rag_database, sandbox_setup, setup_model_registry
from .models.registry import ModelRegistry, AIModel
from .rag.db_cruds import RetrievalDatabaseConnector
from .sandbox.sandbox import Sandbox
# from .workflow_runner import WorkflowRunner

__all__ = [ 
    'Config', 
    'ModelRegistry', 
    'AIModel',
    'RetrievalDatabaseConnector',
    'Sandbox',
    # 'WorkflowRunner',
    'config_setup', 
    'init_rag_database', 
    'sandbox_setup', 
    'setup_model_registry'
]