# (C) 2026 Rodrigo Rodrigues da Silva <rodrigo@flowlexi.com>
# SPDX-License-Identifier: Apache-2.0

"""Python client package for PaveDB."""

from .client import BaseClient, Collection, HttpClient, batch_item, connect
from .errors import (
    Conflict,
    InvalidRequest,
    LocalClientUnavailable,
    NotFoundError,
    PaveError,
    Unavailable,
)

__all__ = [
    "Collection",
    "Conflict",
    "BaseClient",
    "HttpClient",
    "InvalidRequest",
    "LocalClientUnavailable",
    "NotFoundError",
    "PaveError",
    "Unavailable",
    "__version__",
    "batch_item",
    "connect",
]

__version__ = "0.1.0"
