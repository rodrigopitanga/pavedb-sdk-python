# (C) 2026 Rodrigo Rodrigues da Silva <rodrigo@flowlexi.com>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .errors import InvalidRequest

JsonMap = dict[str, Any]


def batch_item(document: object) -> JsonMap:
    """Normalize one text or vector item for ``Collection.add_many``."""
    if isinstance(document, str):
        return {"text": document}
    if isinstance(document, Mapping):
        field = "vector" if "vector" in document else "text"
        item = {
            field: document.get(field),
            "docid": document.get("docid"),
            "metadata": document.get("metadata"),
        }
        if "text" in document and "vector" in document:
            item["text"] = document["text"]
        return item
    if isinstance(document, (tuple, list)):
        if not 1 <= len(document) <= 3:
            raise InvalidRequest(
                "invalid_batch_item",
                "batch items must be text, (text, docid, metadata), or a dict",
            )
        text = document[0]
        docid = document[1] if len(document) > 1 else None
        metadata = document[2] if len(document) > 2 else None
        is_vector = isinstance(text, list) and all(
            isinstance(value, (int, float)) for value in text
        )
        field = "vector" if is_vector else "text"
        return {field: text, "docid": docid, "metadata": metadata}
    raise InvalidRequest(
        "invalid_batch_item",
        "batch items must be text, (text, docid, metadata), or a dict",
    )
