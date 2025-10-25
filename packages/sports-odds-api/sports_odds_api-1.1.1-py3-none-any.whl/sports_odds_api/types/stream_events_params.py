# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["StreamEventsParams"]


class StreamEventsParams(TypedDict, total=False):
    event_id: Annotated[str, PropertyInfo(alias="eventID")]
    """An eventID to stream events for"""

    feed: str
    """The feed you would like to subscribe to"""

    league_id: Annotated[str, PropertyInfo(alias="leagueID")]
    """A leagueID to stream events for"""
