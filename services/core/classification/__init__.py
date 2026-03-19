"""Classification, tagging, watchlist, and summary services."""

from services.core.classification.summary import summarize_tag_group, summarize_watchlist_group
from services.core.classification.tags import add_tag_to_instrument, list_tags_for_instrument, remove_tag_from_instrument
from services.core.classification.watchlists import (
    add_instrument_to_watchlist,
    create_watchlist,
    get_watchlist,
    list_watchlist_items,
    remove_instrument_from_watchlist,
)

__all__ = [
    "add_instrument_to_watchlist",
    "add_tag_to_instrument",
    "create_watchlist",
    "get_watchlist",
    "list_tags_for_instrument",
    "list_watchlist_items",
    "remove_instrument_from_watchlist",
    "remove_tag_from_instrument",
    "summarize_tag_group",
    "summarize_watchlist_group",
]
