# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List
from typing_extensions import TypeAlias

from .shared.airspacecontrolorder_full import AirspacecontrolorderFull

__all__ = ["AirspaceControlOrderTupleResponse"]

AirspaceControlOrderTupleResponse: TypeAlias = List[AirspacecontrolorderFull]
