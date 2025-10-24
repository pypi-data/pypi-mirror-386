"""Deferred post-creation response schema."""

from typing import TypedDict


class DeferredPostCreateResponse(TypedDict):
    """Response from POST /msg/deferred endpoint."""

    deferred_post_id: str  # The ID is returned as string from API


__all__ = ['DeferredPostCreateResponse']
