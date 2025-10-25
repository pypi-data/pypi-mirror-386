"""Data models for Miniflux API."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Feed:
    """Represents a Miniflux feed."""

    id: int
    title: str
    site_url: str
    feed_url: str

    @classmethod
    def from_dict(cls, data: dict) -> "Feed":
        """Create a Feed from API response data."""
        return cls(
            id=data["id"],
            title=data["title"],
            site_url=data["site_url"],
            feed_url=data["feed_url"],
        )


@dataclass
class Entry:
    """Represents a Miniflux feed entry."""

    id: int
    feed_id: int
    title: str
    url: str
    content: str
    feed: Feed
    status: str  # "read" or "unread"
    starred: bool
    published_at: datetime
    original_content: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "Entry":
        """Create an Entry from API response data."""
        return cls(
            id=data["id"],
            feed_id=data["feed_id"],
            title=data["title"],
            url=data["url"],
            content=data["content"],
            feed=Feed.from_dict(data["feed"]),
            status=data["status"],
            starred=data["starred"],
            published_at=datetime.fromisoformat(data["published_at"].replace("Z", "+00:00")),
            original_content=data.get("original_content"),
        )

    @property
    def is_read(self) -> bool:
        """Check if entry is marked as read."""
        return self.status == "read"

    @property
    def is_unread(self) -> bool:
        """Check if entry is marked as unread."""
        return self.status == "unread"
