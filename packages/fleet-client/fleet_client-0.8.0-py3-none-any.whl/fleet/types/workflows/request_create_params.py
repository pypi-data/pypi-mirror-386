# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Required, TypedDict

__all__ = ["RequestCreateParams"]


class RequestCreateParams(TypedDict, total=False):
    url: Required[str]

    camo: bool

    ephemeral_browser: bool

    stealth: bool

    wait_until: Literal["load", "networkidle", "domcontentloaded", "commit"]
