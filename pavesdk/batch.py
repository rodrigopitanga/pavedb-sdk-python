# (C) 2026 Rodrigo Rodrigues da Silva <rodrigo@flowlexi.com>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .errors import InvalidRequest

JsonMap = dict[str, Any]


def batch_item(document: object) -> JsonMap:
    if isinstance(document, str):
        return {"text": document}
    if isinstance(document, Mapping):
        return {
            "text": document.get("text"),
            "docid": document.get("docid"),
            "metadata": document.get("metadata"),
        }
    if isinstance(document, (tuple, list)):
        if not 1 <= len(document) <= 3:
            raise InvalidRequest(
                "invalid_batch_item",
                "batch items must be text, (text, docid, metadata), or a dict",
            )
        text = document[0]
        docid = document[1] if len(document) > 1 else None
        metadata = document[2] if len(document) > 2 else None
        return {"text": text, "docid": docid, "metadata": metadata}
    raise InvalidRequest(
        "invalid_batch_item",
        "batch items must be text, (text, docid, metadata), or a dict",
    )
