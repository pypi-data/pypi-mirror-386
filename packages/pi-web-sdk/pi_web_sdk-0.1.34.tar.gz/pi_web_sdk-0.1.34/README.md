# PI Web API Python SDK

A modular Python SDK for interacting with the OSIsoft PI Web API. The codebase has been reorganised from a single monolithic module into a structured package that groups related controllers, configuration primitives, and the HTTP client.

## Project Description
pi_web_sdk delivers a consistently structured Python interface for AVEVA PI Web API deployments. It wraps the REST endpoints with typed controllers, rich client helpers, and practical defaults so you can query PI data, manage assets, and orchestrate analytics without hand-crafting HTTP calls. The package is organised for extensibility: add new controllers or override behaviours while keeping a cohesive developer experience.

## Features
- **Typed configuration** via `PIWebAPIConfig` and enums for authentication and WebID formats
- **Reusable HTTP client** `PIWebAPIClient` wrapper around `requests.Session` with centralised error handling
- **Domain-organized controllers** split by functionality (system, assets, data, streams, OMF, etc.) for easier navigation
- **Idempotent create_or_get pattern** - Simplified resource creation with automatic fallback to existing resources
- **Default server helpers** - Quick access to default asset and data servers
- **Point enums** - Type-safe enums for PI Point types and classes
- **Stream Updates** for incremental data retrieval without websockets (marker-based polling)
- **OMF support** with ORM-style API for creating types, containers, assets, and hierarchies
- **Comprehensive CRUD operations** for all major PI Web API endpoints
- **Event Frame helpers** - High-level convenience methods for complex event frame operations
- **Parsed responses** - Type-safe response wrappers with generic data classes
- **Advanced search** - AFSearch syntax support for querying elements and attributes
- **Real-time streaming** - WebSocket/SSE channel support for live data updates
- **Bulk operations** - Get/update multiple resources in single API calls
- **108 tests** - Comprehensive test coverage for all controllers
- **Backwards-compatible** `aveva_web_api.py` re-export for existing imports

## Installation
This project depends on `requests`. Install it with:

```bash
pip install requests
```

## Quick Start

### Basic Usage
```python
from pi_web_sdk import AuthMethod, PIWebAPIClient, PIWebAPIConfig

config = PIWebAPIConfig(
    base_url="https://your-pi-server/piwebapi",
    auth_method=AuthMethod.ANONYMOUS,
    verify_ssl=False,  # enable in production
)

client = PIWebAPIClient(config)
print(client.home.get())
```

### Simplified Resource Creation (create_or_get Pattern)

The SDK provides idempotent `create_or_get_*` methods that automatically handle resource creation with fallback to existing resources:

```python
from pi_web_sdk.models import Element, Attribute, Point, PointType, AttributeType

# Get default servers (no need to manually list and select first item)
data_server = client.data_server.get_default()
asset_database = client.asset_database.get_default_database()

# Create or get root element in asset database
plant = client.asset_database.create_or_get_element(
    web_id=asset_database['WebId'],
    element=Element(name="Plant", description="Main plant")
)

# Create or get child elements (builds hierarchy)
area = client.element.create_or_get_element(
    web_id=plant['WebId'],
    element=Element(name="Area1", description="Production area")
)

reactor = client.element.create_or_get_element(
    web_id=area['WebId'],
    element=Element(name="Reactor01", description="Chemical reactor")
)

# Create or get attribute
attribute = Attribute(
    name="Temperature",
    type=AttributeType.DOUBLE.value,
    default_units_name="degC"
)

temp_attr = client.element.create_or_get_attribute(
    web_id=reactor['WebId'],
    attribute=attribute,
    value=25.5  # Optional initial value
)

# Create or get PI Point attribute (creates both PI Point and attribute)
point = Point(
    name="Reactor01_Temp",
    point_type=PointType.FLOAT32,
    engineering_units="degC"
)

pipoint_attr = client.element.create_or_get_pipoint_attribute(
    element_web_id=reactor['WebId'],
    data_server_web_id=data_server['WebId'],
    attribute=Attribute(name="Temperature", type=AttributeType.DOUBLE.value),
    point=point,
    value=22.5
)

# Create or get PI Point directly
pressure_point = client.data_server.create_or_get_point(
    web_id=data_server['WebId'],
    point=Point(
        name="Reactor01_Press",
        point_type=PointType.FLOAT32,
        engineering_units="bar"
    )
)
```

**Benefits:**
- **Idempotent** - Safe to run multiple times
- **No try/except blocks** - Handles errors internally
- **Cleaner code** - Single method call instead of create + fallback logic
- **Automatic PI Point creation** - `create_or_get_pipoint_attribute` creates the PI Point before linking it

**Available create_or_get methods:**
- `client.asset_database.create_or_get_element()` - Root elements
- `client.element.create_or_get_element()` - Child elements
- `client.element.create_or_get_attribute()` - Attributes
- `client.element.create_or_get_pipoint_attribute()` - PI Point attributes (creates PI Point + attribute)
- `client.data_server.create_or_get_point()` - PI Points

See [examples/hierarchy_building_complete.py](examples/hierarchy_building_complete.py) for complete examples.

### Working with Assets
```python
from pi_web_sdk.models.responses import ItemsResponse
from pi_web_sdk.models.asset import Element, Attribute

# List asset servers (parsed response)
servers: ItemsResponse = client.asset_server.list()
server_web_id = servers.items[0].web_id

# Get databases
databases = client.asset_server.get_databases(server_web_id)
db_web_id = databases.items[0].web_id

# Get all elements from a database
elements: ItemsResponse[Element] = client.asset_database.get_elements(
    db_web_id,
    search_full_hierarchy=True,  # Include nested elements
    max_count=1000
)
for elem in elements.items:
    print(f"Element: {elem.name} at {elem.path}")

# Get elements with filters
pumps: ItemsResponse[Element] = client.asset_database.get_elements(
    db_web_id,
    name_filter="Pump*",
    template_name="Equipment"
)

# Get all attributes from an element
attributes: ItemsResponse[Attribute] = client.element.get_attributes(
    element_web_id,
    search_full_hierarchy=False,  # Only direct attributes
    max_count=100
)
for attr in attributes.items:
    print(f"Attribute: {attr.name} = {attr.value}")

# Get attributes with filters
temp_attributes = client.element.get_attributes(
    element_web_id,
    name_filter="Temp*",
    value_type="Float64"
)

# Create an element
element = Element(
    name="MyElement",
    description="Test element",
    template_name="MyTemplate"
)
new_element = client.asset_database.create_element(db_web_id, element)
element_web_id = new_element.web_id

# Create static attributes (values stored in AF)
from pi_web_sdk.models.attribute import Attribute, AttributeType

# String attribute
string_attr = Attribute(
    name="Description",
    type=AttributeType.STRING,
    value="Production Line A"
)
client.element.create_attribute(element_web_id, string_attr)

# Integer attribute
int_attr = Attribute(
    name="MaxCapacity",
    type=AttributeType.INT32,
    value=1000
)
client.element.create_attribute(element_web_id, int_attr)

# Float attribute
float_attr = Attribute(
    name="Efficiency",
    type=AttributeType.DOUBLE,
    value=95.5
)
client.element.create_attribute(element_web_id, float_attr)

# Create dynamic attributes (PI Point references)
# These store data in PI Data Archive

# Get PI Point web IDs first
point_web_id_temp = client.point.get_by_path(r"\\PI_SERVER\Temperature_Tag").web_id
point_web_id_pressure = client.point.get_by_path(r"\\PI_SERVER\Pressure_Tag").web_id

# Temperature attribute (Float, PI Point reference)
temp_attr = Attribute(
    name="Temperature",
    type=AttributeType.DOUBLE,
    data_reference_plug_in="PI Point",
    config_string=point_web_id_temp  # Reference to PI Point
)
client.element.create_attribute(element_web_id, temp_attr)

# Pressure attribute (Integer, PI Point reference)
pressure_attr = Attribute(
    name="Pressure",
    type=AttributeType.INT32,
    data_reference_plug_in="PI Point",
    config_string=point_web_id_pressure
)
client.element.create_attribute(element_web_id, pressure_attr)

# Status attribute (String, PI Point reference)
status_point_web_id = client.point.get_by_path(r"\\PI_SERVER\Status_Tag").web_id
status_attr = Attribute(
    name="Status",
    type=AttributeType.STRING,
    data_reference_plug_in="PI Point",
    config_string=status_point_web_id
)
client.element.create_attribute(element_web_id, status_attr)
```

### Attribute Helper Functions
```python
from typing import Union, Optional
from pi_web_sdk.models.attribute import Attribute, AttributeType

def add_static_attribute(
    client,
    element_web_id: str,
    name: str,
    value: Union[str, int, float],
    description: Optional[str] = None
) -> Attribute:
    """Add a static attribute to an element (value stored in AF)."""

    # Determine type from value
    if isinstance(value, str):
        attr_type = AttributeType.STRING
    elif isinstance(value, int):
        attr_type = AttributeType.INT32
    elif isinstance(value, float):
        attr_type = AttributeType.DOUBLE
    else:
        raise ValueError(f"Unsupported value type: {type(value)}")

    attribute = Attribute(
        name=name,
        type=attr_type,
        value=value,
        description=description
    )

    return client.element.create_attribute(element_web_id, attribute)

def add_dynamic_attribute(
    client,
    element_web_id: str,
    name: str,
    pi_point_path: str,
    value_type: Union[str, int, float] = float,
    description: Optional[str] = None
) -> Attribute:
    """Add a dynamic attribute to an element (PI Point reference)."""

    # Get PI Point web ID
    point = client.point.get_by_path(pi_point_path)
    point_web_id = point.web_id

    # Determine type from value_type parameter
    if value_type == str or value_type == "string":
        attr_type = AttributeType.STRING
    elif value_type == int or value_type == "int":
        attr_type = AttributeType.INT32
    elif value_type == float or value_type == "float":
        attr_type = AttributeType.DOUBLE
    else:
        raise ValueError(f"Unsupported value type: {value_type}")

    attribute = Attribute(
        name=name,
        type=attr_type,
        data_reference_plug_in="PI Point",
        config_string=point_web_id,
        description=description
    )

    return client.element.create_attribute(element_web_id, attribute)

# Usage examples
# Add static attributes
add_static_attribute(client, element_web_id, "Location", "Building 1")
add_static_attribute(client, element_web_id, "Capacity", 5000)
add_static_attribute(client, element_web_id, "Efficiency", 98.7)

# Add dynamic attributes with PI Point references
add_dynamic_attribute(
    client,
    element_web_id,
    "Temperature",
    r"\\PI_SERVER\Temperature_Tag",
    value_type=float,
    description="Process temperature in Celsius"
)

add_dynamic_attribute(
    client,
    element_web_id,
    "Pressure",
    r"\\PI_SERVER\Pressure_Tag",
    value_type=int,
    description="Process pressure in PSI"
)

add_dynamic_attribute(
    client,
    element_web_id,
    "Status",
    r"\\PI_SERVER\Status_Tag",
    value_type=str,
    description="Equipment status"
)
```

### Working with Streams
```python
from pi_web_sdk.models.stream import StreamValue, TimedValue
from datetime import datetime

# Get stream value
value: StreamValue = client.stream.get_value(stream_web_id)
print(f"Current value: {value.value} at {value.timestamp}")

# Get recorded data
recorded = client.stream.get_recorded(
    web_id=stream_web_id,
    start_time="*-7d",
    end_time="*",
    max_count=1000
)

# Get latest value
latest: StreamValue = client.stream.get_end(stream_web_id)

# Get value at specific time
value_at_time = client.stream.get_recorded_at_time(
    stream_web_id,
    "2024-01-01T12:00:00Z",
    retrieval_mode="AtOrBefore"
)

# Get values at multiple times
values = client.stream.get_recorded_at_times(
    stream_web_id,
    ["2024-01-01T00:00:00Z", "2024-01-01T12:00:00Z", "2024-01-02T00:00:00Z"]
)

# Get interpolated values
interpolated = client.stream.get_interpolated_at_times(
    stream_web_id,
    ["2024-01-01T06:00:00Z", "2024-01-01T18:00:00Z"]
)

# Open real-time streaming channel
channel = client.stream.get_channel(
    stream_web_id,
    include_initial_values=True,
    heartbeat_rate=30
)

# Update stream value
new_value = TimedValue(
    timestamp=datetime(2024, 1, 1, 0, 0, 0),
    value=42.5
)
client.stream.update_value(stream_web_id, new_value)

# Bulk operations for multiple streams
latest_values = client.streamset.get_end([stream_id1, stream_id2, stream_id3])
```

### Stream Updates (Incremental Data Retrieval)
```python
import time
from pi_web_sdk.models.stream import StreamUpdateRegistration, StreamUpdates

# Register for stream updates
registration: StreamUpdateRegistration = client.stream.register_update(stream_web_id)
marker = registration.latest_marker

# Poll for incremental updates
while True:
    time.sleep(5)  # Wait between polls

    # Retrieve only new data since last marker
    updates: StreamUpdates = client.stream.retrieve_update(marker)

    for item in updates.items:
        print(f"{item.timestamp}: {item.value}")

    # Update marker for next poll
    marker = updates.latest_marker

# For multiple streams, use streamset
registration = client.streamset.register_updates([stream_id1, stream_id2, stream_id3])
marker = registration.latest_marker

updates = client.streamset.retrieve_updates(marker)
for stream_update in updates.items:
    stream_id = stream_update.web_id
    for item in stream_update.items:
        print(f"Stream {stream_id}: {item.timestamp} = {item.value}")
```

See [examples/README_STREAM_UPDATES.md](examples/README_STREAM_UPDATES.md) for comprehensive Stream Updates documentation.

### OMF (OSIsoft Message Format) Support
```python
from pi_web_sdk.omf import OMFManager
from pi_web_sdk.models.omf import OMFType, OMFProperty, OMFContainer, OMFData
from datetime import datetime

# Initialize OMF manager
omf_manager = OMFManager(client, data_server_web_id)

# Create a type definition
sensor_type = OMFType(
    id="TempSensorType",
    classification="dynamic",
    type="object",
    properties=[
        OMFProperty("timestamp", "string", is_index=True, format="date-time"),
        OMFProperty("temperature", "number", name="Temperature")
    ]
)
omf_manager.create_type(sensor_type)

# Create a container
container = OMFContainer(
    id="sensor1",
    type_id="TempSensorType"
)
omf_manager.create_container(container)

# Send data
data_point = OMFData(
    container_id="sensor1",
    values=[{
        "timestamp": datetime(2024, 1, 1, 0, 0, 0).isoformat() + "Z",
        "temperature": 25.5
    }]
)
omf_manager.send_data(data_point)
```

### OMF Hierarchies
```python
from pi_web_sdk.models.omf import OMFHierarchy, OMFHierarchyNode

# Create hierarchy from paths
hierarchy = OMFHierarchy()
hierarchy.add_path("Plant/Area1/Line1")
hierarchy.add_path("Plant/Area1/Line2")
hierarchy.add_path("Plant/Area2/Line3")

# Or create nodes explicitly
root = OMFHierarchyNode("Plant", "Root")
area1 = OMFHierarchyNode("Area1", "Area", parent=root)
line1 = OMFHierarchyNode("Line1", "Line", parent=area1)

# Deploy hierarchy
omf_manager.create_hierarchy(hierarchy)
```

### Event Frame Helpers
```python
from pi_web_sdk.models.event import EventFrame, EventFrameAttribute
from datetime import datetime

# Create event frame with attributes in one operation
event = EventFrame(
    name="Batch Run 001",
    description="Production batch",
    start_time=datetime(2024, 1, 1, 8, 0, 0),
    end_time=datetime(2024, 1, 1, 16, 0, 0),
    attributes=[
        EventFrameAttribute(name="Temperature", value=95.5),
        EventFrameAttribute(name="Pressure", value=1013.25),
        EventFrameAttribute(name="Status", value="Complete")
    ]
)
created_event = client.event_frame_helpers.create_event_frame_with_attributes(
    db_web_id, event
)

# Create child event frame
child = EventFrame(
    name="Quality Check",
    description="QC inspection",
    start_time=datetime(2024, 1, 1, 15, 30, 0),
    end_time=datetime(2024, 1, 1, 15, 45, 0),
    attributes=[
        EventFrameAttribute(name="Result", value="Pass"),
        EventFrameAttribute(name="Inspector", value="John Doe")
    ]
)
client.event_frame_helpers.create_child_event_frame_with_attributes(
    created_event.web_id, child
)

# Create complete hierarchy
from pi_web_sdk.models.event import EventFrameHierarchy, ChildEventFrame

hierarchy = EventFrameHierarchy(
    root=EventFrame(
        name="Production Run",
        description="Full production cycle",
        start_time=datetime(2024, 1, 1, 8, 0, 0),
        end_time=datetime(2024, 1, 1, 18, 0, 0),
        attributes=[EventFrameAttribute(name="Batch", value="B-2024-001")]
    ),
    children=[
        ChildEventFrame(
            name="Mixing",
            start_time=datetime(2024, 1, 1, 8, 0, 0),
            end_time=datetime(2024, 1, 1, 10, 0, 0),
            attributes=[EventFrameAttribute(name="Speed", value=1200)]
        ),
        ChildEventFrame(
            name="Heating",
            start_time=datetime(2024, 1, 1, 10, 0, 0),
            end_time=datetime(2024, 1, 1, 14, 0, 0),
            attributes=[EventFrameAttribute(name="Target", value=95.0)]
        )
    ]
)
client.event_frame_helpers.create_event_frame_hierarchy(db_web_id, hierarchy)

# Get event frame with all attribute values
event_data = client.event_frame_helpers.get_event_frame_with_attributes(
    event_web_id,
    include_values=True
)
```

See [docs/event_frame_helpers.md](docs/event_frame_helpers.md) for complete documentation.

### Parsed Responses (Type-Safe)
```python
from pi_web_sdk.models.data import DataServer, Point
from pi_web_sdk.models.responses import ItemsResponse

# Get parsed response with type safety
server: DataServer = client.data_server.get_parsed(web_id)
print(f"Server: {server.name}")
print(f"Version: {server.server_version}")
print(f"Connected: {server.is_connected}")

# List with type safety and iteration
servers: ItemsResponse[DataServer] = client.data_server.list_parsed()
for server in servers:
    print(f"{server.name}: {server.path}")

# Get points with type safety
points: ItemsResponse[Point] = client.data_server.get_points_parsed(server_web_id)
for point in points:
    print(f"{point.name} ({point.point_type}): {point.engineering_units}")
```

### Advanced Search (AFSearch Syntax)
```python
from pi_web_sdk.models.asset import Element, AttributeSearch
from pi_web_sdk.models.responses import ItemsResponse

# Query elements by attributes
elements: ItemsResponse[Element] = client.element.get_elements_query(
    database_web_id,
    query="Name:='Pump*' Type:='Equipment'"
)

# Create persistent attribute search
search = AttributeSearch(
    database_web_id=database_web_id,
    query="Name:='Temperature' Type:='Float64'"
)
search_result = client.element.create_search_by_attribute(search)
search_id = search_result.web_id

# Execute search later
results: ItemsResponse[Element] = client.element.execute_search_by_attribute(search_id)

# Bulk get multiple elements
elements: ItemsResponse[Element] = client.element.get_multiple(
    [web_id1, web_id2, web_id3],
    selected_fields="Name;Path;Description"
)
```

### Analysis Operations
```python
from pi_web_sdk.models.analysis import Analysis, AnalysisTemplate, SecurityEntry

# Get analysis with security
analysis: Analysis = client.analysis.get(analysis_web_id)

# Get security entries
entries: ItemsResponse[SecurityEntry] = client.analysis.get_security_entries(analysis_web_id)

# Create security entry
entry = SecurityEntry(
    name="Operators",
    security_identity_web_id=identity_web_id,
    allow_rights=["Read", "Execute"]
)
client.analysis.create_security_entry(analysis_web_id, entry)

# Work with analysis templates
template: AnalysisTemplate = client.analysis_template.get_by_path(
    "\\\\AnalysisTemplate\\MyTemplate"
)
template.description = "Updated"
client.analysis_template.update(template.web_id, template)

# Get analysis categories
categories = client.analysis.get_categories(analysis_web_id)
```

## Available Controllers
All controller instances are available as attributes on `PIWebAPIClient`:

### System & Configuration
- `client.home` - Home endpoint
- `client.system` - System information and status
- `client.configuration` - System configuration

### Asset Model
- `client.asset_server` - Asset servers
- `client.asset_database` - Asset databases
- `client.element` - Elements
- `client.element_category` - Element categories
- `client.element_template` - Element templates
- `client.attribute` - Attributes
- `client.attribute_category` - Attribute categories
- `client.attribute_template` - Attribute templates

### Data & Streams
- `client.data_server` - Data servers
- `client.point` - PI Points
- `client.stream` - Stream data operations (including Stream Updates)
- `client.streamset` - Batch stream operations (including Stream Set Updates)

### Analysis & Events
- `client.analysis` - PI Analyses
- `client.analysis_category` - Analysis categories
- `client.analysis_rule` - Analysis rules
- `client.analysis_rule_plugin` - Analysis rule plugins
- `client.analysis_template` - Analysis templates
- `client.event_frame` - Event frames
- `client.event_frame_helpers` - High-level event frame operations
- `client.table` - PI Tables
- `client.table_category` - Table categories

### OMF
- `client.omf` - OSIsoft Message Format endpoint

### Batch & Advanced
- `client.batch` - Batch operations
- `client.calculation` - Calculations
- `client.channel` - Channels

### Supporting Resources
- `client.enumeration_set` - Enumeration sets
- `client.enumeration_value` - Enumeration values
- `client.unit` - Units of measure
- `client.time_rule` - Time rules
- `client.security` - Security operations
- `client.notification` - Notification rules
- `client.metrics` - System metrics

## Package Layout
- `pi_web_sdk/config.py` - Enums and configuration dataclass
- `pi_web_sdk/exceptions.py` - Custom exception types
- `pi_web_sdk/client.py` - Session management and HTTP helpers
- `pi_web_sdk/controllers/` - Individual controller modules grouped by domain
  - `controllers/base.py` - Base controller with shared utilities
  - `controllers/system.py` - System and configuration controllers
  - `controllers/asset.py` - Asset servers, databases, elements, templates
  - `controllers/attribute.py` - Attributes, categories, templates
  - `controllers/data.py` - Data servers and points (with parsed methods)
  - `controllers/stream.py` - Stream and streamset operations (enhanced)
  - `controllers/analysis.py` - Analysis controllers (fully enhanced)
  - `controllers/event.py` - Event frame controller and high-level helpers
  - `controllers/omf.py` - OMF controller and manager
  - Additional controllers for tables, enumerations, units, security, notifications, etc.
- `pi_web_sdk/models/` - Data models and response classes
  - `models/responses.py` - Generic ItemsResponse[T] and PIResponse[T]
  - `models/data.py` - DataServer and Point models
  - `models/stream.py` - Stream enums (BufferOption, UpdateOption)
  - `models/omf.py` - OMF data models
  - `models/attribute.py` - Attribute models
- `pi_web_sdk/omf/` - OMF support with ORM-style API
  - `omf/orm.py` - Core OMF classes (Type, Container, Asset, Data)
  - `omf/hierarchy.py` - Hierarchy builder utilities
- `docs/` - Comprehensive documentation
- `examples/` - Working code examples
- `tests/` - 108 tests covering all controllers
- `aveva_web_api.py` - Compatibility shim for existing imports

## Extending the SDK
Each controller inherits from `BaseController`, which exposes helper methods and the configured client session. Add new endpoint support by:

1. Create a new controller module under `pi_web_sdk/controllers/`
2. Define data models in `pi_web_sdk/models/`
3. Register controller in `pi_web_sdk/controllers/__init__.py`
4. Add it to `pi_web_sdk/client.py` in the `PIWebAPIClient.__init__` method

Example:
```python
from __future__ import annotations
from typing import Optional
from dataclasses import dataclass
from .base import BaseController
from ..models.responses import PIResponse

@dataclass
class MyResource:
    web_id: str
    name: str
    description: Optional[str] = None

class MyController(BaseController):
    def get(self, web_id: str) -> PIResponse[MyResource]:
        response = self.client.get(f"myresource/{web_id}")
        return PIResponse(MyResource(**response))
```

## Testing
Run the test suite:

```bash
# Run all tests
pytest tests/

# Run specific test files
pytest tests/test_omf_endpoint.py -v

# Run with integration marker
pytest -m integration
```

## Deployment

### Quick Deployment

```bash
# Validate package
python deploy.py --check

# Deploy to TestPyPI (recommended first)
python deploy.py --test

# Deploy to PyPI
python deploy.py --prod
```

### Prerequisites
- PyPI and TestPyPI accounts
- API tokens configured in `~/.pypirc`
- Build tools: `pip install build twine`

See [DEPLOYMENT_QUICKSTART.md](DEPLOYMENT_QUICKSTART.md) for quick start guide or [DEPLOYMENT.md](DEPLOYMENT.md) for comprehensive instructions.

## Documentation & Examples
- [PI Web API Reference](https://docs.aveva.com/bundle/pi-web-api-reference/page/help/getting-started.html)
- [OMF Documentation](https://docs.aveva.com/)
- [Stream Updates Guide](examples/README_STREAM_UPDATES.md) - Comprehensive guide for incremental data retrieval
- [Stream Updates Examples](examples/stream_updates_example.py) - Working code examples
- [Event Frame Helpers Documentation](docs/event_frame_helpers.md) - High-level event frame operations
- [Parsed Responses Documentation](docs/parsed_responses.md) - Type-safe response wrappers
- [Controller Additions Summary](docs/CONTROLLER_ADDITIONS_SUMMARY.md) - Complete list of all enhancements
- See `examples/` directory for more usage examples

## Recent Additions

### Idempotent Resource Creation (v2025.10.09)
Major usability improvement with `create_or_get` pattern and helper methods:

**create_or_get Methods**
- `asset_database.create_or_get_element()` - Create or get root elements
- `element.create_or_get_element()` - Create or get child elements
- `element.create_or_get_attribute()` - Create or get attributes
- `element.create_or_get_pipoint_attribute()` - Create PI Point and attribute in one call
- `data_server.create_or_get_point()` - Create or get PI Points

**Default Server Helpers**
- `data_server.get_default()` - Get default data server (first in list)
- `asset_server.get_default()` - Get default asset server (first in list)

**Point Enums** - Type-safe enums for PI Point configuration
- `PointType` - FLOAT32, FLOAT64, INT16, INT32, DIGITAL, TIMESTAMP, STRING, BLOB
- `PointClass` - BASE, CLASSIC

**Key Benefits:**
- Idempotent operations - safe to run multiple times
- No manual try/except blocks needed
- Automatic PI Point creation before attribute linking
- Simplified hierarchy building

See the "Simplified Resource Creation" section and [examples/hierarchy_building_complete.py](examples/hierarchy_building_complete.py) for complete documentation.

### Comprehensive Controller Enhancements (v2025.10)
Major enhancement to the SDK with 78 new methods and 108 tests covering the full PI Web API surface:

**Analysis Controllers** (46 methods)
- Full CRUD operations for analyses, templates, categories, rules, and plugins
- Security management (get, create, update, delete security entries)
- Category associations
- Analysis rule management

**Element Enhancements** (7 methods)
- `get_multiple()` - Bulk retrieval of elements
- `get_elements_query()` - AFSearch syntax support for powerful queries
- `create_search_by_attribute()` / `execute_search_by_attribute()` - Persistent searches
- `add_referenced_element()` / `remove_referenced_element()` - Reference management
- `get_notification_rules()` / `create_notification_rule()` - Notification support

**Stream Enhancements** (11 methods)
- `get_end()` - Latest recorded value
- `get_recorded_at_time()` / `get_recorded_at_times()` - Point-in-time retrieval
- `get_interpolated_at_times()` - Interpolated values at specific times
- `get_channel()` - Real-time WebSocket/SSE streaming channels
- All methods available for single streams (`StreamController`) and multiple streams (`StreamSetController`)

**Event Frame Helpers** (6 methods)
- `create_event_frame_with_attributes()` - Create event frame and attributes in one call
- `create_child_event_frame_with_attributes()` - Create child with attributes
- `create_event_frame_hierarchy()` - Build complete hierarchies
- `get_event_frame_with_attributes()` - Retrieve with all attribute values
- `update_event_frame_attributes()` - Bulk attribute updates
- `close_event_frame()` - Close with optional value capture

**Parsed Responses** (Type-safe data classes)
- Generic `ItemsResponse[T]` and `PIResponse[T]` wrappers
- Support for iteration, indexing, and len()
- Added `*_parsed()` methods to DataServer and Point controllers
- Automatic deserialization to typed objects

See [docs/CONTROLLER_ADDITIONS_SUMMARY.md](docs/CONTROLLER_ADDITIONS_SUMMARY.md) for complete details.

### Stream Updates (v2025.01)
Stream Updates provides an efficient way to retrieve incremental data updates without websockets. Key features:
- **Marker-based tracking** - Maintains position in data stream
- **Single or multiple streams** - Support for individual streams and stream sets
- **Metadata change detection** - Notifies when data is invalidated
- **Unit conversion** - Convert values during retrieval
- **Selected fields** - Filter response data
- **Type-safe data classes** - Strongly typed response models

```python
from pi_web_sdk.models.stream import StreamUpdateRegistration, StreamUpdates

# Register once
registration: StreamUpdateRegistration = client.stream.register_update(stream_web_id)
marker = registration.latest_marker

# Poll repeatedly for new data only
while True:
    time.sleep(5)
    updates: StreamUpdates = client.stream.retrieve_update(marker)
    # Process updates.items with type safety
    for item in updates.items:
        print(f"{item.timestamp}: {item.value}")
    marker = updates.latest_marker
```

**Requirements**: PI Web API 2019+ with Stream Updates feature enabled

See [examples/README_STREAM_UPDATES.md](examples/README_STREAM_UPDATES.md) for complete documentation.

## License
See LICENSE file for details.

