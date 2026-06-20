# (C) 2026 Rodrigo Rodrigues da Silva <rodrigo@flowlexi.com>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations


class PaveError(RuntimeError):
    """Base PaveDB client error."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class NotFoundError(PaveError):
    """Requested resource was not found."""


class InvalidRequest(PaveError):
    """Request shape or arguments are invalid."""


class Conflict(PaveError):
    """Request conflicts with existing state."""


class Unavailable(PaveError):
    """The server or an underlying dependency is unavailable."""


class LocalClientUnavailable(InvalidRequest):
    """A local target was requested without a local provider installed."""


_ERROR_TYPES = {
    "not_found": NotFoundError,
    "invalid": InvalidRequest,
    "conflict": Conflict,
    "unavailable": Unavailable,
}


def error_class(code: str, error_type: str | None = None) -> type[PaveError]:
    """Return the best client exception class for a PaveDB error code."""
    if error_type in _ERROR_TYPES:
        return _ERROR_TYPES[error_type]
    if code in {"auth_invalid", "auth_forbidden"}:
        return InvalidRequest
    if code == "embedder_unavailable" or code.endswith("_unavailable"):
        return Unavailable
    if code.endswith("_not_found") or code in {"not_found", "query_not_found"}:
        return NotFoundError
    if "conflict" in code or code.endswith("_exists"):
        return Conflict
    if code.startswith("invalid_") or code.endswith("_invalid"):
        return InvalidRequest
    return PaveError
