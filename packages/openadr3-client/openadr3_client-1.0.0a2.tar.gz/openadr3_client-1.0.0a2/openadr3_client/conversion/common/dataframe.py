from typing import final

try:
    import pandera.pandas as pa
    from pandera.engines.pandas_engine import DateTime
    from pandera.typing import Series, Timedelta
except ImportError as e:
    msg = (
        "DataFrame conversion functionality requires the 'pandas' extra. "
        "Install it with: pip install 'openadr3-client[pandas]' or the equivalent in your package manager."
    )
    raise ImportError(msg) from e


@final
class EventIntervalDataFrameSchema(pa.DataFrameModel):
    """Pandera schema for an event interval dataframe input."""

    # IntervalPeriod fields (flattened)
    start: Series[DateTime(time_zone_agnostic=True)] | None = pa.Field(nullable=True)  # type: ignore[reportInvalidTypeForm, valid-type]
    duration: Series[Timedelta] | None = pa.Field(nullable=True)
    randomize_start: Series[Timedelta] | None = pa.Field(nullable=True)

    # EventPayload fields (flattened)
    type: Series[str]  # Enum type not directly supported with pandera, but pydantic will validate this later on.
    values: Series[pa.Object]  # Type validation will be done by pydantic later.

    class Config:
        strict = "filter"  # Filter out any columns not specified in the schema here.

    @pa.check("values")
    def payload_values_atleast_one(self, values: Series) -> Series[bool]:
        """Check that the values are a list and have at least one element."""
        return values.map(lambda v: isinstance(v, list) and len(v) > 0)  # type: ignore[return-value]
