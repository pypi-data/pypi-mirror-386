# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime
from typing_extensions import Literal

from .._models import BaseModel

__all__ = ["MonitorResponse"]


class MonitorResponse(BaseModel):
    monitor_id: str
    """A unique monitor ID."""

    name: str
    """Name of the monitor."""

    created_at: Optional[datetime] = None
    """The time the monitor was created in UTC."""

    description: Optional[str] = None
    """Description of the monitor."""

    monitor_status: Optional[Literal["active", "inactive"]] = None
    """Status of the monitor.

    Can be `active` or `inactive`. Inactive monitors no longer record and evaluate
    events.
    """

    updated_at: Optional[datetime] = None
    """The most recent time the monitor was modified in UTC."""

    user_id: Optional[str] = None
    """User ID of the user who created the monitor."""
