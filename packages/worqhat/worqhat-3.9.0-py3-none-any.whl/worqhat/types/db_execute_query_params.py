# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union
from typing_extensions import Literal, Required, TypedDict

from .._types import SequenceNotStr

__all__ = ["DBExecuteQueryParams"]


class DBExecuteQueryParams(TypedDict, total=False):
    query: Required[str]
    """SQL query to execute.

    Supports both named parameters ({param}) and positional parameters ($1, $2)
    """

    environment: Literal["development", "staging", "production"]
    """Environment to query (development, staging, production)"""

    params: Union[Dict[str, object], SequenceNotStr[Union[str, float, bool]]]
    """Named parameters for queries with {param} syntax"""
