# (C) 2026 Rodrigo Rodrigues da Silva <rodrigo@flowlexi.com>
# SPDX-License-Identifier: Apache-2.0

"""Python SDK package for PaveDB."""

from .batch import batch_item
from .client import HttpClient, connect
from .compat import PAVEDB_API_PREFIX, PAVEDB_API_VERSION
from .errors import (
    Conflict,
    InvalidRequest,
    LocalClientUnavailable,
    NotFoundError,
    PaveError,
    Unavailable,
)
from .interface import BaseClient, Collection

__all__ = [
    "BaseClient",
    "Collection",
    "Conflict",
    "HttpClient",
    "InvalidRequest",
    "LocalClientUnavailable",
    "NotFoundError",
    "PaveError",
    "PAVEDB_API_PREFIX",
    "PAVEDB_API_VERSION",
    "Unavailable",
    "__version__",
    "batch_item",
    "connect",
]

__version__ = "0.1.1"
