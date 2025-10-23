from datetime import datetime, timedelta
from typing import TypedDict

from openadr3_client.models._base_model import BaseModel
from openadr3_client.models.common.payload import AllowedPayloadInputs


class _EventIntervalDictRequiredFields(TypedDict):
    """
    Required dictionary keys for event interval dict.

    Separated from the optional parameters, as Optional[X] still requires the key to be present
    in the dictionary. While we want them to be omittable.
    """

    # EventPayload fields (flattened)
    type: str
    values: list[AllowedPayloadInputs]


class EventIntervalDictInput(_EventIntervalDictRequiredFields, total=False):
    """
    TypedDict for the event interval input.

    Inherits the required fields which are required inside the dictionary, all the keys
    defined here are optional.
    """

    # IntervalPeriod fields (flattened)
    start: datetime | None
    duration: timedelta | None
    randomize_start: timedelta | None


class EventIntervalDictPydanticValidator(BaseModel):
    """Pydantic validator for the event interval dict."""

    start: datetime | None = None
    duration: timedelta | None = None
    randomize_start: timedelta | None = None

    type: str
    values: list[AllowedPayloadInputs]
