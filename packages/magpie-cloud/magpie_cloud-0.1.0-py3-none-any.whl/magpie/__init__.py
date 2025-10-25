"""
Magpie SDK for MicroVM Orchestrator
"""

from .client import Magpie
from .exceptions import (
    MagpieError,
    AuthenticationError,
    JobNotFoundError,
    TemplateNotFoundError,
    ValidationError,
    APIError,
)
from .models import (
    Job,
    JobRun,
    JobStatus,
    JobResult,
    Template,
    LogEntry,
    PersistentVMHandle,
    SSHCommandResult,
)

__version__ = "0.1.0"
__all__ = [
    "Magpie",
    "MagpieError",
    "AuthenticationError",
    "JobNotFoundError",
    "TemplateNotFoundError",
    "ValidationError",
    "APIError",
    "Job",
    "JobRun",
    "JobStatus",
    "JobResult",
    "Template",
    "LogEntry",
    "PersistentVMHandle",
    "SSHCommandResult",
]
