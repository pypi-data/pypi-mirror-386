# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, TypedDict

from .wait_until import WaitUntil

__all__ = ["RequestCreateParams"]


class RequestCreateParams(TypedDict, total=False):
    url: Required[str]

    camo: bool

    ephemeral_browser: bool

    stealth: bool

    wait_until: WaitUntil
