"""
Magpie Cloud - Create runtime workers and code sandboxes.
Visit https://magpiecloud.com for more information.
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

__version__ = "0.1.1"
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
