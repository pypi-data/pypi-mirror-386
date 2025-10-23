"""Contains the domain types related to events."""

from __future__ import annotations

from abc import ABC
from typing import final

from pydantic import AwareDatetime, Field, NonNegativeInt, field_validator

from openadr3_client.models._base_model import BaseModel
from openadr3_client.models.common.creation_guarded import CreationGuarded
from openadr3_client.models.common.interval import Interval
from openadr3_client.models.common.interval_period import IntervalPeriod
from openadr3_client.models.common.target import Target
from openadr3_client.models.event.event_payload import EventPayload, EventPayloadDescriptor
from openadr3_client.models.model import OpenADRResource


class Event(ABC, OpenADRResource):
    """Base class for events."""

    program_id: str = Field(alias="programID", min_length=1, max_length=128)
    """Identifier of the program this event belongs to."""

    event_name: str | None = None
    """The name of the event."""

    priority: NonNegativeInt | None = None
    """The priority of the event, less is higher priority."""

    targets: tuple[Target, ...] | None = None
    """The targets of the event."""

    payload_descriptors: tuple[EventPayloadDescriptor, ...] | None = None
    """The payload descriptors of the event."""

    interval_period: IntervalPeriod | None = None
    """The interval period of the event."""

    intervals: tuple[Interval[EventPayload], ...]
    """The intervals of the event."""

    @property
    def name(self) -> str | None:
        """Helper method to get the name field of the model."""
        return self.event_name


@final
class EventUpdate(BaseModel):
    """Class representing an update to an existing event."""

    program_id: str | None = Field(alias="programID", default=None, min_length=1, max_length=128)
    """Identifier of the program this event belongs to."""

    event_name: str | None = None
    """The name of the event."""

    priority: NonNegativeInt | None = None
    """The priority of the event, less is higher priority."""

    targets: tuple[Target, ...] | None = None
    """The targets of the event."""

    payload_descriptors: tuple[EventPayloadDescriptor, ...] | None = None
    """The payload descriptors of the event."""

    interval_period: IntervalPeriod | None = None
    """The interval period of the event."""

    intervals: tuple[Interval[EventPayload], ...] | None = None
    """The intervals of the event."""


@final
class NewEvent(Event, CreationGuarded):
    """Class representing a new event not yet pushed to the VTN."""

    @field_validator("intervals", mode="after")
    @classmethod
    def atleast_one_interval(cls, intervals: tuple[Interval, ...]) -> tuple[Interval, ...]:
        """
        Validates that an event has at least one interval defined.

        Args:
            intervals (tuple[Interval, ...]): The intervals of the event.

        """
        if len(intervals) == 0:
            err_msg = "NewEvent must contain at least one interval."
            raise ValueError(err_msg)
        return intervals


class ServerEvent(Event):
    """Class representing an event retrieved from the VTN."""

    id: str
    """The identifier for the event."""

    created_date_time: AwareDatetime
    modification_date_time: AwareDatetime


@final
class ExistingEvent(ServerEvent):
    """Class representing an existing event retrieved from the VTN."""

    def update(self, update: EventUpdate) -> ExistingEvent:
        """
        Update this event with the provided update.

        Args:
            update: The update to apply to this event.

        Returns:
            A new ExistingEvent instance with the updates applied.

        """
        current_data = self.model_dump()
        update_data = update.model_dump(exclude_unset=True)
        updated_data = current_data | update_data
        return ExistingEvent(**updated_data)


@final
class DeletedEvent(ServerEvent):
    """Class representing a deleted event."""
