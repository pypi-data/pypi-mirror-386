# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict
from typing_extensions import TypedDict

__all__ = ["FlowTriggerWithPayloadParams"]


class FlowTriggerWithPayloadParams(TypedDict, total=False):
    data: Dict[str, object]
    """Optional structured data to pass to the workflow"""
