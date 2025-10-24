"""Wrapper for GEM collection event link."""
from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from .collection_event import CollectionEvent
    from .collection_event_report import CollectionEventReport


class CollectionEventLink:
    """Representation for registered/linked collection event."""

    def __init__(self,
                 collection_event: CollectionEvent,
                 reports: list[CollectionEventReport],
                 **kwargs):
        """Initialize a collection event link.

        Args:
            collection_event: collection event
            reports: list of the linked reports
            **kwargs: additional attributes for object

        """
        self._collection_event = collection_event
        self._reports = reports
        self.enabled = False

        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def collection_event(self) -> CollectionEvent:
        """Get the associated collection event."""
        return self._collection_event

    @property
    def reports(self):
        """Get list of the data values.

        Returns:
            List of linked reports

        """
        return self._reports
