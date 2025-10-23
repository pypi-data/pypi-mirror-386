[![CodeQL](https://github.com/ElaadNL/openadr3-client/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/ElaadNL/openadr3-client/actions/workflows/github-code-scanning/codeql)
[![Python Default CI](https://github.com/ElaadNL/openadr3-client/actions/workflows/ci.yml/badge.svg)](https://github.com/ElaadNL/openadr3-client/actions/workflows/ci.yml)
![PYPI-DL](https://img.shields.io/pypi/dm/openadr3-client?style=flat)
[![image](https://img.shields.io/pypi/v/openadr3-client?label=pypi)](https://pypi.python.org/pypi/openadr3-client)
[![Python Versions](https://img.shields.io/pypi/pyversions/openadr3-client)](https://pypi.python.org/pypi/openadr3-client)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)

# OpenADR3 Client

This library provides two main interfaces for interacting with OpenADR3 (Open Automated Demand Response) systems:

1. Business Logic (BL) Client - For VTN operators (for example, DSOs).
2. Virtual End Node (VEN) Client - For end users (for example, device operators).

## Business Logic (BL) Client

The BL client is designed for VTN operators to manage OpenADR3 programs and events. It provides full control over the following interfaces:

- **Events**: Create, read, update, and delete events
- **Programs**: Create, read, update, and delete programs
- **Reports**: Read-only access to reports
- **VENS**: Read-only access to VEN information
- **Subscriptions**: Read-only access to subscriptions

### Example BL Usage

```python
from datetime import UTC, datetime, timedelta

from openadr3_client.bl.http_factory import BusinessLogicHttpClientFactory
from openadr3_client.models.common.unit import Unit
from openadr3_client.models.event.event import EventPayload, Interval, NewEvent
from openadr3_client.models.event.event_payload import EventPayloadType
from openadr3_client.models.program.program import (
    EventPayloadDescriptor,
    IntervalPeriod,
    NewProgram,
    Target,
)

# Initialize the client with the required OAuth configuration.
bl_client = BusinessLogicHttpClientFactory.create_http_bl_client(
    vtn_base_url="https://vtn.example.com",
    client_id="your_client_id",
    client_secret="your_client_secret", 
    token_url="https://auth.example.com/token",
    scopes=["read_all", "write_events", "write_programs"]  # Optional: specify required scopes
)

# Create a new program (NewProgram allows for more properties, this is just a simple example).
program = NewProgram(
        id=None, # ID cannot be set by the client, assigned by the VTN.
        program_name="Example Program",
        program_long_name="Example Program Long Name",
        interval_period=IntervalPeriod(
            start=datetime(2023, 1, 1, 12, 30, 0, tzinfo=UTC),
            duration=timedelta(minutes=5),
            randomize_start=timedelta(minutes=5),
        ),
        payload_descriptor=(EventPayloadDescriptor(payload_type=EventPayloadType.PRICE, units=Unit.KWH, currency="EUR"),),
        targets=(Target(type="test-target-1", values=("test-value-1",)),),
)

created_program = bl_client.programs.create_program(new_program=program)

# Create an event inside the program
event = NewEvent(
    id=None,
    programID=created_program.id, # ID of program is known after creation
    event_name="test-event",
    priority=999,
    targets=(Target(type="test-target-1", values=("test-value-1",)),),
    payload_descriptor=(
        EventPayloadDescriptor(payload_type=EventPayloadType.PRICE, units=Unit.KWH, currency="EUR"),
    ),
    # Top Level interval definition, each interval specified with the None value will inherit this
    # value by default as its interval period. In this case, each interval will have an implicit
    # duration of 5 minutes.
    interval_period=IntervalPeriod(
        start=datetime(2023, 1, 1, 12, 30, 0, tzinfo=UTC),
        duration=timedelta(minutes=5),
    ),
    intervals=(
        Interval(
            id=0,
            interval_period=None,
            payloads=(EventPayload(type=EventPayloadType.PRICE, values=(2.50,)),),
        ),
    ),
)

created_event = bl_client.events.create_event(new_event=event)


```

## Virtual End Node (VEN) Client

The VEN client is designed for end users and device operators to receive and process OpenADR3 programs and events. It provides:

- **Events**: Read-only access to events
- **Programs**: Read-only access to programs
- **Reports**: Create and manage reports
- **VENS**: Register and manage VEN information
- **Subscriptions**: Manage subscriptions to programs and events

### Example VEN Client Usage

```python
from openadr3_client.ven.http_factory import VirtualEndNodeHttpClientFactory

# Initialize the client with the required OAuth configuration.
ven_client = VirtualEndNodeHttpClientFactory.create_http_ven_client(
    vtn_base_url="https://vtn.example.com",
    client_id="your_client_id",
    client_secret="your_client_secret",
    token_url="https://auth.example.com/token",
    scopes=["read_all", "write_reports"]  # Optional: specify required scopes
)

# Search for events inside the VTN.
events = ven_client.events.get_events(target=..., pagination=..., program_id=...)

# Process the events as needed...
```

## Data Format Conversion

The library provides convenience methods to convert between OpenADR3 event intervals and common data formats. These conversions can be used both for input (creating event intervals from a common data format) and output (processing existing event intervals to a common data format).

### Pandas DataFrame Format

The library supports conversion between event intervals and pandas DataFrames. The DataFrame format is validated using a `pandera` schema to ensure data integrity.

> **Note:** DataFrame conversion functionality requires the optional `pandas` extra. Install it with:
> ```bash
> pip install 'openadr3-client[pandas]'
> ```
> or the equivalent in your package manager

#### Pandas Input Format

When creating an event interval from a DataFrame, the input must match the following schema:

| Column Name | Type | Required | Description |
|------------|------|----------|-------------|
| type | str | Yes | The type of the event interval |
| values | list[Union[int, float, str, bool, Point]] | Yes | The payload values for the interval |
| start | datetime64[ns, UTC] | Yes | The start time of the interval (UTC timezone) |
| duration | timedelta64[ns] | Yes | The duration of the interval |
| randomize_start | timedelta64[ns] | No | The randomization window for the start time |

Important notes:

- All datetime values must be timezone-aware and in UTC
- All datetime and timedelta values must use nanosecond precision (`[ns]`)
- The id column of an event interval cannot be provided as input - the client will automatically assign incrementing integer IDs to the event intervals, in the same order as they were given.

Example DataFrame:

```python
import pandas as pd

df = pd.DataFrame({
    'type': ['SIMPLE'],
    'values': [[1.0, 2.0]],
    'start': [pd.Timestamp("2023-01-01 00:00:00.000Z").as_unit("ns")],
    'duration': [pd.Timedelta(hours=1)],
    'randomize_start': [pd.Timedelta(minutes=5)]
})
```

#### Pandas Output Format

When converting an event interval to a DataFrame, the output will match the same schema as the input format, with one addition: the event interval's `id` field will be included as the DataFrame index. The conversion process includes validation to ensure the data meets the schema requirements, including timezone and precision specifications.

### TypedDict Format

The library also supports conversion between event intervals and lists of dictionaries using a TypedDict format.

#### Dictionary Input Format

When creating an event interval from a dictionary, the input must follow the `EventIntervalDictInput` format:

| Field Name | Type | Required | Description |
|------------|------|----------|-------------|
| type | str | Yes | The type of the event interval |
| values | list[Union[int, float, str, bool, Point]] | Yes | The payload values for the interval |
| start | datetime | No | The start time of the interval (must be timezone aware) |
| duration | timedelta | No | The duration of the interval |
| randomize_start | timedelta | No | The randomization window for the start time |

Important notes:

- All datetime values must be timezone-aware and in UTC
- The id field cannot be provided as input - the client will automatically assign incrementing integer IDs to the event intervals, in the same order as they were given

Example input:

```python
from datetime import datetime, timedelta, UTC

dict_iterable_input = [
    {
        # Required fields
        'type': 'SIMPLE',
        'values': [1.0, 2.0],
        
        # Optional fields
        'start': datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
        'duration': timedelta(hours=1),
        'randomize_start': timedelta(minutes=15)
    },
]
```

#### Dictionary Output Format

When converting an event interval to a list of dictionaries, the output is checked against the `EventIntervalDictInput` TypedDict with type hints to ensure compliance. The output is a list of `EventIntervalDictInput` values.

## Getting Started

1. Install the package
2. Configure the required environment variables
3. Choose the appropriate client interface (BL or VEN)
4. Initialize the client with the required interfaces
5. Start interacting with the OpenADR3 VTN system.

## Model Immutability

All domain models defined in the openadr3-client are immutable by design. This is enforced through Pydantic's `frozen = True` configuration. This means that once a model instance is created, its properties cannot be modified directly.

To make changes to an existing resource (like a Program or VEN), you must use the `update` method provided by the corresponding `Existing{ResourceName}` class. This method takes an update object that contains only the properties that are valid to be altered.

For example, to update a program:

```python
existing:program : ExistingProgram = ...

# Create an update object with the properties you want to change
program_update = ProgramUpdate(
    program_name="Updated Program Name",
    program_long_name="Updated Program Long Name"
)

# Apply the update to an existing program, this returns a new ExistingProgram object with the update changes applied.
updated_program = existing_program.update(program_update)
```

This pattern ensures data consistency and makes it clear which properties can be modified after creation.

## Custom Enumeration Cases

The library supports both predefined and custom enumeration cases for various types like `Unit`, `EventPayloadType`, and `ReportPayloadType`. This flexibility allows for adherence to the OpenADR3 specification, which specifies both common default enumeration values, while also allowing for arbitrary custom values.

To support this as best as possible, ensuring type safety and ease of use through the standard enum interface for these common cases, the choice was made to extend the enumeration classes and allow for dynamic case construction only when needed for custom values.

### Predefined Cases

Predefined enumeration cases are type-safe and can be used directly:

```python
from openadr3_client.models.common.unit import Unit
from openadr3_client.models.event.event_payload import EventPayloadDescriptor, EventPayloadType

# Using predefined cases
unit = Unit.KWH
payload_type = EventPayloadType.SIMPLE

# These can be used in payload descriptors
descriptor = EventPayloadDescriptor(
    payload_type=unit,
    units=payload_type
)
```

### Custom Cases

To use custom enumeration cases, you must use the functional constructor. The library will validate and create a new enumeration case dynamically:

```python
from openadr3_client.models.common.unit import Unit
from openadr3_client.models.event.event_payload import EventPayloadDescriptor, EventPayloadType

# Using custom cases
custom_unit = Unit("CUSTOM_UNIT")
custom_payload_type = EventPayloadType("CUSTOM_PAYLOAD")

# These can be used in payload descriptors
descriptor = EventPayloadDescriptor(
    payload_type=custom_payload_type,
    units=custom_unit
)
```

Note that custom enumeration cases are validated according to the OpenADR3 specification:

- For `EventPayloadType`, values must be strings between 1 and 128 characters
- For `ReportPayloadType`, values must be strings between 1 and 128 characters
- For `Unit`, any string value is accepted

## Creation Guard Pattern

All `New{Resource}` classes (such as `NewProgram`, `NewVen`, etc.) inherit from the `CreationGuarded` class. This implements a creation guard pattern that ensures each instance can only be used to create a resource in the VTN exactly once.

This pattern prevents accidental reuse of creation objects, which could lead to duplicate resources or unintended side effects. If you attempt to use the same `New{Resource}` instance multiple times to create a resource, the library will raise a `ValueError`.

For example:

```python
# Create a new program instance
new_program = NewProgram(
    program_name="Example Program",
    program_long_name="Example Program Long Name",
    # ... other required fields ...
)

# First creation - this will succeed
created_program = bl_client.programs.create_program(new_program=new_program)

# Second creation with the same instance - this will raise ValueError
try:
    duplicate_program = bl_client.programs.create_program(new_program=new_program)
except ValueError as e:
    print(f"Error: {e}")  # Will print: "Error: CreationGuarded object has already been created."
```

## Validator Plugins

openadr3-client supports the use of validator plugins. The plugins are created using the ValidatorPlugin class, which contains a set of validators for a model.

### Registering a plugin

Registering a plugin is done using the global ValidatorPluginRegistry class:

```python
    from openadr3_client.plugin import ValidatorPluginRegistry, ValidatorPlugin
    from openadr3_client.models.event.event import Event

    ValidatorPluginRegistry.register_plugin(
        MyFirstPlugin().setup()
    ).register_plugin(
        MySecondPlugin().setup()
    )
```

Since the ValidatorPluginRegistry class is a singleton, all validators will run after the registration.

### Creating a plugin

To see how to create a plugin, see the doc-comment on the ValidatorPlugin class.

### GAC compliance plugin

The GAC compliance plugin is a first-party plugin available [here](https://github.com/ElaadNL/openadr3-client-gac-compliance) which adds additional domain validation rules to the OpenADR3 domain models to enforce compliance with the Dutch GAC (Grid Aware Charging) specification.

## Development

- To run all linters and formatters with automatic fixes applied
```sh
poetry run task fix
```

- To run tests
```sh
poetry run task test
```

- To dry run ci locally (no automatic fixes applied)
```sh
poetry run task local-ci
```

### Testing

#### Prerequisites

- Allow usage of the Docker Socket
    - MacOS: advanced settings ??
    - Linux: check if you are part of the Docker user group `groups $USER | grep docker`, otherwise add yourself to it `sudo usermod -aG docker $USER`

### Running the tests

1. Have the Docker Deamon running
2. (`poetry install`)
3. `poetry run pytest`
