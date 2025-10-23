"""Couchbase Infrastructure Automation Package.

A Python library and CLI tool for automating Couchbase Capella infrastructure setup,
including projects, clusters, databases, and AI models.
"""

from importlib.metadata import version

try:
    __version__ = version("couchbase-infrastructure")
except Exception:
    __version__ = "unknown"

__author__ = "Couchbase"

from couchbase_infrastructure.client import CapellaClient
from couchbase_infrastructure.config import CapellaConfig
from couchbase_infrastructure.resources import (
    create_project,
    create_free_cluster,
    create_developer_pro_cluster,
    create_database_user,
    deploy_ai_model,
    load_sample_data,
)

__all__ = [
    "CapellaClient",
    "CapellaConfig",
    "create_project",
    "create_free_cluster",
    "create_developer_pro_cluster",
    "create_database_user",
    "deploy_ai_model",
    "load_sample_data",
]
