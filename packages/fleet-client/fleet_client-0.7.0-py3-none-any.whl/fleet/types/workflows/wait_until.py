# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing_extensions import Literal, TypeAlias

__all__ = ["WaitUntil"]

WaitUntil: TypeAlias = Literal["load", "networkidle", "domcontentloaded", "commit"]
