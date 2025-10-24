# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Required, TypedDict

__all__ = ["AsyncCreateJobParams"]


class AsyncCreateJobParams(TypedDict, total=False):
    url: Required[str]

    stealth: bool

    wait_until: Literal["load", "networkidle", "domcontentloaded", "commit"]
