# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List
from typing_extensions import TypeAlias

from .shared.conjunction_full import ConjunctionFull

__all__ = ["ConjunctionTupleResponse"]

ConjunctionTupleResponse: TypeAlias = List[ConjunctionFull]
