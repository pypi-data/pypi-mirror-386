# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Required, TypedDict

__all__ = ["SessionVisitPageParams"]


class SessionVisitPageParams(TypedDict, total=False):
    url: Required[str]

    wait_until: Literal["load", "networkidle", "domcontentloaded", "commit"]
