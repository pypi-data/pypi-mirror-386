# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable
from typing_extensions import Required, TypedDict

from .elset_ingest_param import ElsetIngestParam

__all__ = ["ElsetUnvalidatedPublishParams"]


class ElsetUnvalidatedPublishParams(TypedDict, total=False):
    body: Required[Iterable[ElsetIngestParam]]
