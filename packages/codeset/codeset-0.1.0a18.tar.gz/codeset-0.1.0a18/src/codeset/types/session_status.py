# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing_extensions import Literal, TypeAlias

__all__ = ["SessionStatus"]

SessionStatus: TypeAlias = Literal["creating", "ready", "busy", "error", "closed"]
