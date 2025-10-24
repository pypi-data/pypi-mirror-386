# Cognite Typed Functions

Enterprise-grade framework for building type-safe, composable Cognite Functions with automatic validation, built-in introspection, and AI integration.

## Why Cognite Typed Functions?

Standard [Cognite Functions](https://docs.cognite.com/cdf/functions/) require a simple `handle(client, data)` function, which becomes unwieldy for complex APIs. This framework provides composable architecture, automatic validation, and built-in introspection.

**Standard Cognite Function:**

```python
def handle(client, data):
    try:
        asset_no = int(data["assetNo"])  # Manual validation
        include_tax = data.get("includeTax", "false").lower() == "true"  # Manual parsing
        # Handle routing manually based on data
        if data.get("action") == "get_item":
            # Implementation here
        elif data.get("action") == "create_item":
            # Different implementation
    except Exception as e:
        return {"error": str(e)}  # Basic error handling
```

**With Typed Functions:**

```python
@app.get("/items/{item_id}")
def get_item(client: CogniteClient, item_id: int, include_tax: bool = False) -> ItemResponse:
    """Retrieve an item by ID"""
    # Type validation and coercion handled automatically
    # Clear function signature with proper types
    # Automatic error handling and response formatting
```

## Features

- **Type-safe routing** - Decorator-based syntax (`@app.get()`, `@app.post()`, etc.) with automatic validation
- **Async/await support** - Write both sync and async handlers for concurrent operations
- **Automatic type validation** - Recursive conversion of nested data structures with Pydantic models
- **OpenAPI schema generation** - Auto-generated API documentation
- **Built-in introspection** - `/__schema__`, `/__routes__`, `/__health__`, `/__ping__` endpoints
- **Model Context Protocol (MCP)** - Native AI tool exposure for LLM integration
- **Comprehensive error handling** - Structured error responses with detailed information
- **Enterprise logging** - Isolated logger with dependency injection across all cloud providers
- **Distributed tracing** - OpenTelemetry-based tracing with automatic span creation and OTLP export
- **Composable architecture** - Build modular services from reusable middleware apps
- **Path and query parameters** - Support for dynamic URL parameters and query strings
- **Modern Python** - Python 3.10+ with union types (`x | None`), builtin generics
- **Full Cognite Functions compatibility** - Works with scheduling, secrets, and all deployment methods

## Quick Start

### Installation

**Requirements:**

- Python 3.10 or higher
- uv (recommended) or pip

```bash
# Install the package (when published)
# pip install cognite-typed-functions

# Optional: Install with tracing support
# pip install cognite-typed-functions[tracing]
```

### Basic Example

```python
# No typing imports needed - using builtin generic types
from cognite.client import CogniteClient
from pydantic import BaseModel

from cognite_typed_functions import FunctionApp, create_function_service

# Create your app
app = FunctionApp(title="My API", version="1.0.0")

# Define your models
class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None

class ItemResponse(BaseModel):
    id: int
    item: Item
    total_price: float

# Define your endpoints
@app.get("/items/{item_id}")
def get_item(
    client: CogniteClient,
    item_id: int,
    include_tax: bool = False
) -> ItemResponse:
    """Retrieve an item by ID"""
    item = Item(
        name=f"Item {item_id}",
        price=100.0,
        tax=10.0 if include_tax else None
    )
    total = item.price + (item.tax or 0)
    return ItemResponse(id=item_id, item=item, total_price=total)

@app.post("/items/")
def create_item(client: CogniteClient, item: Item) -> ItemResponse:
    """Create a new item"""
    new_id = 12345  # Your creation logic here
    total = item.price + (item.tax or 0)
    return ItemResponse(id=new_id, item=item, total_price=total)

@app.post("/process/batch")
def process_batch(client: CogniteClient, items: list[Item]) -> dict:
    """Process multiple items in batch"""
    total_value = sum(item.price + (item.tax or 0) for item in items)
    return {"processed_count": len(items), "total_value": total_value}

# Export the handler for Cognite Functions
handle = create_function_service(app)
```

## Local Development

Test your functions locally using uvicorn before deploying to Cognite:

```python
# dev.py
from cognite_typed_functions.devserver import create_asgi_app
from handler import handle

app = create_asgi_app(handle)
```

Then run:

```bash
uv run uvicorn dev:app --reload
```

For complete setup instructions, environment variables, and troubleshooting, see [Local Development Server Guide](docs/dev-server.md).

## Error Handling

The framework provides structured error handling with detailed information for debugging:

- **RouteNotFound** - No matching route found
- **ValidationError** - Input validation failed
- **TypeConversionError** - Parameter type conversion failed
- **ExecutionError** - Function execution failed

All error responses follow a consistent structure:

```python
{
    "success": false,
    "error_type": "ValidationError",
    "message": "Input validation failed: 1 error(s)",
    "details": {"errors": [...]}
}
```

Success responses are similarly structured:

```python
{
    "success": true,
    "data": {...}  # Your actual response data
}
```

## Logging

The framework provides an enterprise-grade logging solution that works across all cloud providers through dependency injection.

### Why Use the Framework Logger?

According to the [Cognite Functions documentation](https://docs.cognite.com/cdf/functions/), the standard Python `logging` module is not recommended because it can interfere with the cloud provider's logging infrastructure. This framework provides an **isolated logger** that:

- Uses Python's standard `logging` module with familiar API
- Writes directly to stdout (captured by all cloud providers)
- Is completely isolated from other loggers
- Supports standard log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Can be dependency-injected like `client` and `secrets`
- Works with both sync and async handlers

### Logger Usage

Add `logger: logging.Logger` to your function signature:

```python
import logging
from cognite.client import CogniteClient
from cognite_typed_functions import FunctionApp

app = FunctionApp(title="My API", version="1.0.0")

@app.get("/items/{item_id}")
def get_item(client: CogniteClient, logger: logging.Logger, item_id: int) -> dict:
    """Retrieve an item with logging"""
    logger.info(f"Fetching item {item_id}")
    item = fetch_item(item_id)
    logger.debug(f"Item details: {item}")
    return {"id": item_id, "name": item.name}
```

### Log Levels

```python
@app.post("/process/data")
def process_data(client: CogniteClient, logger: logging.Logger, data: dict) -> dict:
    logger.debug("Detailed debug information")      # DEBUG: Detailed diagnostic info
    logger.info("Processing started")               # INFO: General informational messages
    logger.warning("Unexpected value encountered")  # WARNING: Warning messages
    logger.error("Processing failed")               # ERROR: Error messages
    logger.critical("System failure")               # CRITICAL: Critical errors
    return {"status": "processed"}
```

By default, the logger is configured at **INFO** level.

### Async Handlers

The logger works seamlessly with async handlers:

```python
@app.post("/process/batch")
async def process_batch(
    client: CogniteClient,
    logger: logging.Logger,
    items: list[Item]
) -> dict:
    logger.info(f"Starting batch processing of {len(items)} items")

    async def process_item(item: Item) -> dict:
        logger.debug(f"Processing item: {item.name}")
        result = await process_async(item)
        return result

    results = await asyncio.gather(*[process_item(item) for item in items])
    logger.info(f"Batch processing complete. Processed {len(results)} items")
    return {"processed_count": len(results), "results": results}
```

### Logging Best Practices

- **Use appropriate log levels**: DEBUG for diagnostics, INFO for normal operation, WARNING for unexpected situations, ERROR for failures, CRITICAL for severe errors
- **Don't log sensitive information**: Avoid logging credentials, tokens, or personal data
- **Use structured logging**: Include relevant context in log messages
- **Log at key points**: Entry points, success paths, and error conditions

## Tracing

The framework provides built-in distributed tracing support through the `TracingApp`, which uses OpenTelemetry to capture execution traces and exports them to an OTLP-compatible collector (like LightStep, Jaeger, or any OpenTelemetry backend).

**Note:** Tracing support requires the optional `tracing` dependencies:

```bash
pip install cognite-typed-functions[tracing]
```

### Why Use Tracing?

Tracing helps you:

- **Understand execution flow** - See how requests flow through your code
- **Identify performance bottlenecks** - Find slow operations in your function
- **Debug production issues** - Trace through complex operations with context
- **Monitor system behavior** - Analyze patterns across function executions
- **Track dependencies** - See how different services interact

### Basic Tracing Usage

Add `TracingApp` to your composed apps and inject `FunctionTracer` into your handlers:

```python
from cognite_typed_functions import (
    FunctionApp,
    FunctionTracer,
    create_function_service,
    create_tracing_app,
)

app = FunctionApp(title="My API", version="1.0.0")

# Configure tracing with OTLP endpoint
tracing = create_tracing_app(
    otlp_endpoint="http://localhost:8360",  # LightStep Satellite or other OTLP collector
    insecure=True  # For local development
)

@app.get("/items/{item_id}")
def get_item(
    client: CogniteClient,
    tracer: FunctionTracer,  # Injected by TracingApp
    item_id: int
) -> dict:
    """Retrieve an item with detailed tracing"""

    # Create child spans for specific operations
    with tracer.span("fetch_from_cdf"):
        item = client.assets.retrieve(id=item_id)

    with tracer.span("process_data"):
        # Your processing logic here
        result = {"id": item.id, "name": item.name}

    return result

# Compose with tracing app
handle = create_function_service(tracing, app)
```

### Automatic Root Spans

**Root spans are automatically created for every request** by the `TracingApp` middleware. You don't need any decorator for this - just compose with the tracing app:

```python
# Root span is automatically created for ALL requests when you compose with TracingApp
handle = create_function_service(tracing, app)
```

Each root span includes:

- HTTP method and route template (e.g., `GET /items/{item_id}`)
- Function ID and call ID (from Cognite Functions runtime)
- Request timestamp and duration
- Success/error status

### Optional Handler-Level Child Spans

Use the `@tracing.trace()` decorator to create a **child span** for specific handlers:

```python
@app.get("/items/{item_id}")
@tracing.trace()  # OPTIONAL: Creates a child span under the automatic root span
def get_item(
    client: CogniteClient,
    tracer: FunctionTracer,
    item_id: int,
    include_details: bool = False
) -> dict:
    """
    Span hierarchy:
    - Root span (automatic): GET /items/{item_id}
      - Handler child span (from @trace()): get_item
        - Grandchild spans (from tracer.span()): fetch_item, fetch_details
    """

    # Create grandchild spans for business logic operations
    with tracer.span("fetch_item"):
        item = client.assets.retrieve(id=item_id)

    if include_details:
        with tracer.span("fetch_details"):
            # Fetch additional details
            pass

    return item.dump()
```

**Note:** The `@tracing.trace()` decorator is optional. It provides additional granularity for specific handlers that need detailed tracing. Most applications only need the automatic root spans.

### Trace Export

Traces are automatically exported to your configured OTLP collector using the OpenTelemetry Protocol (OTLP) over gRPC. Supported backends include:

- **LightStep** - Use LightStep Satellite for local development or LightStep cloud for production
- **Jaeger** - Popular open-source tracing backend with excellent UI
- **Zipkin** - Lightweight distributed tracing system
- **OpenTelemetry Collector** - Vendor-agnostic telemetry data receiver and exporter
- **Any OTLP-compatible backend** - Works with any service supporting OTLP/gRPC

### Trace Structure

Each trace includes:

- **Trace ID** - Unique identifier for the entire request
- **Span ID** - Unique identifier for each operation
- **Parent Span ID** - Links spans into a hierarchy
- **Timestamps** - Start and end times for each operation
- **Attributes** - HTTP method, path, function metadata
- **Status** - Success or error state

### Tracing Best Practices

- **Use descriptive span names**: `"fetch_user_data"` not `"step1"`
- **Create spans for logical operations**: Database queries, API calls, complex calculations
- **Don't over-trace**: Too many tiny spans create noise
- **Add attributes for context**: `tracer.span("process_batch").set_attribute("batch_size", len(items))`
- **Trace at business logic boundaries**: Not every function call, but each significant operation

### Async Handler Support

Tracing works seamlessly with async handlers:

```python
@app.get("/items/{item_id}")
@tracing.trace()
async def get_item_async(
    client: CogniteClient,
    tracer: FunctionTracer,
    item_id: int
) -> dict:
    """Async handler with tracing"""

    async def fetch_details():
        with tracer.span("fetch_details"):
            await asyncio.sleep(0.1)
            return {"extra": "data"}

    async def fetch_reviews():
        with tracer.span("fetch_reviews"):
            await asyncio.sleep(0.1)
            return {"reviews": []}

    # Concurrent operations are traced
    details, reviews = await asyncio.gather(
        fetch_details(),
        fetch_reviews()
    )

    return {"item_id": item_id, "details": details, "reviews": reviews}
```

## Dependency Injection

The framework uses dependency injection to provide framework dependencies (`client`, `secrets`, `logger`, `function_call_info`) to your handlers. You can also **register your own custom dependencies** for services like database connections, tracing, caching, or any other resources your application needs.

### Dependency Matching Semantics

The framework uses **AND semantics** for dependency matching, providing clear and predictable behavior:

**Framework Dependencies (Strict Matching):**

- `client` - Requires **both** `param_name="client"` AND `target_type=CogniteClient`
- `secrets` - Requires **both** `param_name="secrets"` AND `target_type=Mapping` (accepts `dict`, `Mapping`, `dict[str, str]`, `Mapping[str, str]`, etc.)
- `logger` - Requires **both** `param_name="logger"` AND `target_type=logging.Logger`
- `function_call_info` - Requires **both** `param_name="function_call_info"` AND `target_type=FunctionCallInfo`

**Custom Dependencies (Flexible Matching):**

Note: `target_type` is **always required** - this is a typed functions framework.

- Register with `target_type` only for flexible parameter naming (works with any parameter name)
- Register with **both** `param_name` and `target_type` to require BOTH (strict matching with AND logic)

### Registering Custom Dependencies

To use custom dependencies, create a registry with your dependencies and pass it to `create_function_service()`:

```python
from cognite_typed_functions import (
    FunctionApp,
    create_function_service,
    create_default_registry,
)
import redis
import httpx

# Create a custom registry with your dependencies
registry = create_default_registry()

# Register with name+type matching (both required for consistent naming)
registry.register(
    provider=lambda ctx: redis.Redis.from_url(ctx.get("secrets", {}).get("REDIS_URL")),
    target_type=redis.Redis,
    param_name="cache",
    description="Redis cache connection"
)

registry.register(
    provider=lambda ctx: httpx.Client(base_url="https://api.example.com"),
    target_type=httpx.Client,
    param_name="http",
    description="HTTP client for external API"
)

# Create your app
app = FunctionApp(title="My API", version="1.0.0")

# Now use them in your handlers with the registered parameter names
@app.get("/items/{item_id}")
def get_item(
    client: CogniteClient,        # Framework: requires name="client" + type
    cache: redis.Redis,            # Custom: requires name="cache" + type
    http: httpx.Client,            # Custom: requires name="http" + type
    item_id: int
) -> dict:
    # Try cache first
    cached = cache.get(f"item:{item_id}")
    if cached:
        return json.loads(cached)

    # Fetch from external API
    response = http.get(f"/items/{item_id}")
    item_data = response.json()

    # Cache and return
    cache.set(f"item:{item_id}", json.dumps(item_data), ex=3600)
    return item_data

# All endpoints must use the same parameter names consistently
@app.get("/users/{user_id}")
def get_user(
    client: CogniteClient,
    cache: redis.Redis,            # Must use "cache", not "redis_conn"
    http: httpx.Client,            # Must use "http", not "api_client"
    user_id: int
) -> dict:
    # Same dependencies with consistent parameter names across all endpoints
    return {"user_id": user_id}

# Pass the registry to create_function_service
handle = create_function_service(app, registry=registry)
```

### Context-Aware Dependencies

Provider functions receive a context dictionary with `client`, `secrets`, and `function_call_info`:

```python
from cognite_typed_functions import (
    FunctionApp,
    create_function_service,
    create_default_registry,
)

class MyAPIClient:
    def __init__(self, api_key: str, environment: str):
        self.api_key = api_key
        self.environment = environment

    def fetch_data(self):
        # Implementation here
        pass

# Create registry and register with name+type matching (both required)
registry = create_default_registry()
registry.register(
    provider=lambda ctx: MyAPIClient(
        api_key=ctx.get("secrets", {}).get("API_KEY"),
        environment=ctx.get("secrets", {}).get("ENV", "production")
    ),
    target_type=MyAPIClient,
    param_name="api_client",
    description="External API client with credentials"
)

app = FunctionApp(title="My API", version="1.0.0")

@app.post("/sync-data")
def sync_data(
    client: CogniteClient,      # Framework dependency
    api_client: MyAPIClient,    # Custom dependency (must use param_name="api_client")
    data: dict
) -> dict:
    # api_client is initialized with secrets from context
    external_data = api_client.fetch_data()
    # Process and return
    return {"synced": True}

# Pass the registry to create_function_service
handle = create_function_service(app, registry=registry)
```

### Registry Sharing in Composed Apps

When composing multiple apps, **all apps share a single dependency registry**. Built-in framework apps like `TracingApp` automatically register their dependencies (like `FunctionTracer`) into the shared registry:

```python
from cognite_typed_functions import create_function_service
from cognite_typed_functions.mcp import create_mcp_app
from cognite_typed_functions.introspection import create_introspection_app

# Main app with custom dependencies
app = FunctionApp(title="My API", version="1.0.0")
app.registry.register(
    provider=lambda ctx: trace.get_tracer("my-app"),
    target_type=trace.Tracer,
    param_name="tracer",
    description="OpenTelemetry tracer"
)

# Create your main app
app = FunctionApp(title="My API", version="1.0.0")

@app.get("/items/{item_id}")
def get_item(client: CogniteClient, tracer: FunctionTracer, item_id: int) -> dict:
    """Main business endpoint with tracer"""
    with tracer.span("fetch_item_details"):
        return client.assets.retrieve(id=item_id).dump()

# Create extension apps
tracing_app = create_tracing_app()  # Provides FunctionTracer dependency
mcp_app = create_mcp_app()
introspection_app = create_introspection_app()

# Compose apps - FunctionTracer is now available to all apps!
handle = create_function_service(tracing_app, introspection_app, mcp_app, app)

# Now MCP tools can also use 'tracer' with the same parameter name
@mcp_app.tool("Get item with tracing")
def get_item_tool(client: CogniteClient, tracer: FunctionTracer, item_id: int) -> dict:
    with tracer.span("mcp_get_item"):
        # FunctionTracer from TracingApp is available here!
        return client.assets.retrieve(id=item_id).dump()
```

**Note:** `TracingApp` also provides a `@tracing.trace()` decorator for automatic root span creation. See `examples/handler.py` for complete tracing examples.

**If you don't pass a custom registry**, `create_function_service()` creates a default registry with the built-in framework dependencies (`client`, `secrets`, `logger`, `function_call_info`). This is sufficient for most use cases.

### Built-in Dependencies

The framework provides these dependencies by default:

- **`client: CogniteClient`** - Requires **both** parameter name `client` AND type annotation `CogniteClient`
- **`secrets: Mapping[str, str]`** - Requires **both** parameter name `secrets` AND Mapping-compatible type (accepts `dict`, `Mapping`, `dict[str, str]`, `Mapping[str, str]`, etc.)
- **`logger: logging.Logger`** - Requires **both** parameter name `logger` AND type annotation `logging.Logger`
- **`function_call_info: FunctionCallInfo`** - Requires **both** parameter name `function_call_info` AND type annotation `FunctionCallInfo`

These are always available and can be combined with your custom dependencies.

**Important:** Framework dependencies enforce strict naming to match Cognite Functions conventions. You **must** use the exact parameter names with proper type annotations.

## Async Support

The framework supports both synchronous and asynchronous route handlers, enabling efficient concurrent code when needed.

### Why Use Async?

Async handlers are particularly useful for:

- **Concurrent API calls** - Fetch data from multiple sources simultaneously
- **I/O-bound operations** - Database queries, file operations, network requests
- **Parallel processing** - Process multiple items concurrently
- **External service integration** - Call multiple external APIs in parallel

### Basic Async Usage

Simply declare your route handler as `async def` instead of `def`:

```python
import asyncio
from cognite_typed_functions import FunctionApp

app = FunctionApp(title="Async API", version="1.0.0")

# Synchronous handler (traditional)
@app.get("/items/{item_id}")
def get_item(client: CogniteClient, item_id: int) -> ItemResponse:
    """Synchronous data retrieval"""
    # Your sync logic here
    return ItemResponse(...)

# Asynchronous handler (new!)
@app.get("/items/{item_id}/async")
async def get_item_async(client: CogniteClient, item_id: int) -> ItemResponse:
    """Asynchronous data retrieval with concurrent operations"""
    # Use await for async operations
    result = await fetch_data_async(item_id)
    return ItemResponse(...)
```

### Concurrent Operations Example

The real power of async comes from running multiple operations concurrently:

```python
@app.get("/items/{item_id}/details")
async def get_item_with_details(client: CogniteClient, item_id: int) -> dict:
    """Fetch item data from multiple sources concurrently"""

    # Define async operations
    async def fetch_item_info():
        # Simulate API call
        await asyncio.sleep(0.1)
        return {"name": f"Item {item_id}", "price": 100.0}

    async def fetch_inventory():
        # Simulate another API call
        await asyncio.sleep(0.1)
        return {"stock": 50, "warehouse": "A"}

    async def fetch_reviews():
        # Simulate yet another API call
        await asyncio.sleep(0.1)
        return {"rating": 4.5, "count": 120}

    # Execute all operations concurrently (not sequentially!)
    item_info, inventory, reviews = await asyncio.gather(
        fetch_item_info(),
        fetch_inventory(),
        fetch_reviews()
    )

    return {
        "item": item_info,
        "inventory": inventory,
        "reviews": reviews
    }
```

### Batch Processing with Async

Process multiple items concurrently for better performance:

```python
@app.post("/process/batch/async")
async def process_batch_async(client: CogniteClient, items: list[Item]) -> dict:
    """Process multiple items concurrently"""

    async def process_item(item: Item) -> dict:
        """Process a single item asynchronously"""
        # Simulate async processing (e.g., API call, database query)
        await asyncio.sleep(0.01)
        total = item.price + (item.tax or 0)
        return {"name": item.name, "total": total}

    # Process all items concurrently
    results = await asyncio.gather(*[process_item(item) for item in items])

    total_value = sum(result["total"] for result in results)
    return {
        "processed_count": len(items),
        "total_value": total_value,
        "items": results
    }
```

### How It Works

The framework automatically detects whether your handler is sync or async:

- **Async handlers** (`async def`) are awaited directly for native async execution
- **Sync handlers** (`def`) are run on a thread pool to avoid blocking the event loop
- **MCP tools** support both sync and async handlers seamlessly
- **App composition** works with any mix of sync and async handlers

### Performance Considerations

**When async helps:**

- Multiple I/O operations that can run in parallel
- External API calls that can be concurrent
- Database queries that can be batched

**When sync is fine:**

- Simple CPU-bound calculations
- Single database/API call
- Straightforward data transformations

**Note:** Since Cognite Functions don't handle concurrent requests within the same process (each function call gets its own compute instance), async is primarily beneficial for **concurrent operations within a single request**, not for handling multiple requests simultaneously.

### Mixing Sync and Async

You can freely mix sync and async handlers in the same app:

```python
app = FunctionApp(title="Mixed API", version="1.0.0")

@app.get("/simple")
def simple_endpoint(client: CogniteClient) -> dict:
    """Simple sync endpoint"""
    return {"status": "ok"}

@app.get("/complex")
async def complex_endpoint(client: CogniteClient) -> dict:
    """Complex async endpoint with concurrent operations"""
    results = await asyncio.gather(
        fetch_data_1(),
        fetch_data_2(),
        fetch_data_3()
    )
    return {"results": results}

# Both work seamlessly in the same app!
handle = create_function_service(app)
```

## Type Safety and Validation

The framework provides comprehensive type safety with automatic validation and conversion:

- **Input validation** - Pydantic models validate request data
- **Output validation** - Response models ensure consistent output format
- **Type coercion** - Automatic conversion of string parameters to correct types
- **Detailed error messages** - Validation errors include precise paths for debugging

### Basic Type Conversions

- `str` → `int` / `float` / `bool` (accepts "true", "1", "yes", "on")
- `dict` → `BaseModel` - Automatic instantiation with validation
- `list[dict]` → `list[BaseModel]` - Converts lists of dictionaries to model instances

### Recursive Type Conversions

The framework handles arbitrarily nested combinations:

```python
# Complex nested types supported
dict[str, BaseModel]                    # Dict with model values
Optional[BaseModel]                     # Optional models
Union[BaseModel, str]                   # Union types with fallback
list[dict[str, BaseModel]]              # List of dicts of models
dict[str, list[BaseModel]]              # Dict containing lists of models

# Real-world example
class User(BaseModel):
    name: str
    age: int

class Team(BaseModel):
    name: str
    leader: User                        # Nested model
    members: list[User]                 # List of models

@app.post("/teams")
def create_team(client: CogniteClient, team: Team) -> TeamResponse:
    # Input automatically converted:
    # {
    #   "name": "Engineering",
    #   "leader": {"name": "Alice", "age": 30},      # → User instance
    #   "members": [                                 # → list[User]
    #     {"name": "Bob", "age": 25},                # → User instance
    #     {"name": "Carol", "age": 28}               # → User instance
    #   ]
    # }
    return TeamResponse(id=team.name, members_count=len(team.members))
```

### Type Annotation Compatibility

The framework supports both legacy and modern Python type annotation syntaxes:

```python
# Union Types - both work identically
from typing import Union
def process(client: CogniteClient, data: Union[User, str]) -> Response: ...
def process(client: CogniteClient, data: User | str) -> Response: ...

# Optional Types - both work identically
from typing import Optional
def get_user(client: CogniteClient, user: Optional[User]) -> Response: ...
def get_user(client: CogniteClient, user: User | None) -> Response: ...

# Collection Types - both work identically
from typing import List, Dict
def process_items(client: CogniteClient, items: List[Item]) -> Dict[str, int]: ...
def process_items(client: CogniteClient, items: list[Item]) -> dict[str, int]: ...
```

## Introspection

One of the key challenges with standard Cognite Functions is that they become "black boxes" after deployment. This framework solves that problem with built-in introspection endpoints.

### Available Endpoints

- **`/__schema__`** - Returns the complete OpenAPI 3.0 schema for all composed apps
- **`/__routes__`** - Returns a summary of all available routes with descriptions
- **`/__health__`** - Returns health status and comprehensive app information
- **`/__ping__`** - Simple connectivity check for monitoring and pre-warming

### Benefits

- **No more redeployments** just to check function signatures
- **AI tools can discover** and generate code for your functions
- **Team members can easily** understand deployed functions
- **Documentation stays in sync** with implementation

### Example Usage

```bash
# Get complete API documentation
curl "https://your-function-url" -d '{"path": "/__schema__", "method": "GET"}'

# List all available endpoints
curl "https://your-function-url" -d '{"path": "/__routes__", "method": "GET"}'

# Check function health
curl "https://your-function-url" -d '{"path": "/__health__", "method": "GET"}'
```

### Cross-App Introspection

When composing multiple apps, introspection endpoints show routes from all apps:

```json
// /__schema__ response includes routes from all apps
{
  "info": {
    "title": "Your Main App",      // From main_app (last in composition)
    "version": "1.0.0"
  },
  "paths": {
    "/__mcp_tools__": {...},       // From MCP app
    "/__schema__": {...},          // From introspection app
    "/your/business/route": {...}  // From main business app
  }
}
```

## Model Context Protocol (MCP)

The framework includes built-in Model Context Protocol support, enabling AI assistants to discover and use your Cognite Functions as tools.

### MCP Endpoints

- **`/__mcp_tools__`** - List all available MCP tools with their schemas
- **`/__mcp_call__/{tool_name}`** - Execute a specific MCP tool by name

### Usage

```python
from cognite_typed_functions import FunctionApp, create_function_service
from cognite_typed_functions.mcp import create_mcp_app
from cognite_typed_functions.introspection import create_introspection_app

# Create your main business app
app = FunctionApp(title="Asset Management API", version="1.0.0")

@app.get("/items/{item_id}")
def get_item(client: CogniteClient, item_id: int) -> ItemResponse:
    """Retrieve an item by ID"""
    # Your implementation here

# Create MCP app for AI tool exposure
mcp = create_mcp_app("asset-management-tools")

# Use @mcp.tool() decorator to expose specific routes to AI
@mcp.tool()
@app.get("/items/{item_id}")
def get_item_for_ai(client: CogniteClient, item_id: int) -> ItemResponse:
    """AI-accessible version of get_item"""
    return get_item(client, item_id)

# Create introspection app
introspection = create_introspection_app()

# Compose all apps
handle = create_function_service(mcp, introspection, app)
```

### MCP Capabilities

- **Selective exposure** - Use `@mcp.tool()` to choose which endpoints are accessible to AI
- **Automatic schema generation** - AI gets JSON schemas for all parameters and responses
- **Built-in validation** - Input validation happens automatically
- **Tool discovery** - AI can discover available tools via `/__mcp_tools__`
- **Tool execution** - AI can call tools via `/__mcp_call__/{tool_name}`

## App Composition

> **Note:** This is an advanced feature for framework extensibility. Most developers won't need to use app composition directly - it's primarily used internally for features like MCP integration and introspection endpoints. For typical use cases, simply create one `FunctionApp` and add your routes.

The framework supports composing multiple apps together to create modular services.

### Composition Architecture

Apps are composed using left-to-right evaluation for routing, with the last app providing metadata (title, version):

```python
from cognite_typed_functions import FunctionApp, create_function_service
from cognite_typed_functions.introspection import create_introspection_app

# Create individual apps
introspection_app = create_introspection_app()
main_app = FunctionApp("Asset Management API", "2.1.0")

@main_app.get("/assets/{asset_id}")
def get_asset(client: CogniteClient, asset_id: int) -> dict:
    return {"id": asset_id, "name": f"Asset {asset_id}"}

# Compose apps
handle = create_function_service(introspection_app, main_app)
```

### Composition Benefits

- **Cross-app introspection** - `/__schema__` and `/__routes__` show routes from all composed apps
- **Unified metadata** - Uses the last app (main business app) for title/version
- **Routing precedence** - Earlier apps in composition handle routes first
- **Modular design** - Separate system utilities from business logic

## API Reference

### FunctionApp

The main application class for building composable Cognite Function services.

```python
app = FunctionApp(title="My API", version="1.0.0")
```

#### Decorators

- `@app.get(path)` - Handle GET requests (data retrieval)
- `@app.post(path)` - Handle POST requests (create resources). Also to handle generic operations that don't fit REST semantics (batch processing, calculations, transformations)
- `@app.put(path)` - Handle PUT requests (update/replace resources)
- `@app.delete(path)` - Handle DELETE requests (remove resources)

#### When to Use Each Decorator

**Use `@app.get()`** for:

- Retrieving data: `@app.get("/assets/{asset_id}")`
- Listing resources: `@app.get("/assets")`
- Health checks: `@app.get("/health")`

**Use `@app.post()`** for:

- Creating new resources: `@app.post("/assets")`
- Uploading data: `@app.post("/files/upload")`
- Batch processing: `@app.post("/process/batch")`
- Complex calculations: `@app.post("/calculate/metrics")`
- Data transformations: `@app.post("/transform/timeseries")`
- Operations that don't fit CRUD patterns

**Use `@app.put()`** for:

- Updating existing resources: `@app.put("/assets/{asset_id}")`
- Replacing configurations: `@app.put("/settings")`

**Use `@app.delete()`** for:

- Removing resources: `@app.delete("/assets/{asset_id}")`
- Cleanup operations: `@app.delete("/cache")`

#### Parameters

All endpoint functions must accept `client: CogniteClient` as the first parameter. Additional parameters can be:

- **Path parameters**: `{item_id}` in the URL path
- **Query parameters**: URL query string parameters
- **Request body**: Pydantic models for POST/PUT requests

**Parameter Injection and Override Behavior:**

The framework automatically injects certain parameters into endpoint functions. Currently, this includes the `client: CogniteClient` parameter which is automatically provided as the first parameter to all endpoint functions.

If users provide parameters with the same names in their request arguments (through query parameters, path parameters, or request body), the framework will attempt to override the injected values with strict type validation. The provided values must be convertible to the expected parameter types, or a validation error will be raised.

```python
@app.get("/example/{count}")
def example_endpoint(client: CogniteClient, name: str, count: int) -> dict:
    # client is normally the injected CogniteClient instance

    # Parameter override examples:
    # {"name": "test", "count": "123"}         ✅ Works - valid conversions
    # {"name": "test", "count": "abc"}         ❌ ValidationError - cannot convert "abc" to int
    # {"client": "invalid", "name": "test"}    ❌ ValidationError - cannot convert string to CogniteClient

    return {"message": f"Hello {name}, count: {count}"}
```

### create_function_service

Creates a service handler from one or more composed apps. This is the main entry point for converting your FunctionApp instances into a service compatible with Cognite Functions.

```python
from cognite_typed_functions import create_function_service, create_default_registry

# Single app with default dependencies
handle = create_function_service(app)

# Multiple apps (composition)
handle = create_function_service(mcp_app, introspection_app, main_app)

# With custom registry (for custom dependencies)
registry = create_default_registry()
registry.register(
    provider=lambda ctx: my_custom_service(),
    target_type=MyServiceType,
    param_name="my_service",
    description="Custom service"
)
handle = create_function_service(mcp_app, introspection_app, main_app, registry=registry)
```

#### Function Signature

```python
def create_function_service(
    *apps: FunctionApp,
    registry: DependencyRegistry | None = None
) -> Handler:
    """Create handler for single app or composed apps.

    Args:
        *apps: Single FunctionApp or sequence of FunctionApps to compose.
               For composed apps, routing tries each app left-to-right until one matches.
        registry: Optional custom DependencyRegistry with your custom dependencies.
                  If not provided, a default registry with built-in framework dependencies
                  (client, secrets, logger, function_call_info) is created.

    Returns:
        Handler function compatible with Cognite Functions
    """
```

#### App Composition Rules

1. **Routing Order**: Apps are tried **left-to-right** for route matching
2. **Metadata Source**: The **last app** provides title/version for schemas and health checks
3. **Context Sharing**: All apps get composition context, can override method if they need it
4. **Simplicity**: Clean method calls, no complex protocols or type checking overhead

#### Composition Patterns

**System + Business Pattern:**

```python
# Introspection provides system endpoints, main_app provides business logic
handle = create_function_service(introspection_app, main_app)
```

**Full Stack Pattern:**

```python
# Complete composition: AI tools + debugging + business logic
handle = create_function_service(mcp_app, introspection_app, main_app)
```

**Development Pattern:**

```python
# Add debugging capabilities to any existing handler
debug_handle = create_function_service(introspection_app, existing_app)
```

### Request Format

Cognite Functions receive requests in this format:

```python
{
    "path": "/items/123?include_tax=true&q=search",
    "method": "GET",
    "body": {...}  # Optional request body
}
```

### Response Format

All responses follow a structured format:

```python
# Success response
{
    "success": true,
    "data": {...}  # Your actual response data
}

# Error response
{
    "success": false,
    "error_type": "ValidationError",
    "message": "Input validation failed: 1 error(s)",
    "details": {"errors": [...]}
}
```

## Architecture

The framework is organized into several modules:

- **`app.py`** - Core application class and request handling with FastAPI-style decorators
- **`models.py`** - Shared Pydantic models for responses, errors, and request parsing
- **`schema.py`** - OpenAPI schema generation utilities
- **`introspection.py`** - Core introspection endpoints (schema, routes, health)
- **`mcp.py`** - Model Context Protocol integration and AI tool exposure
- **`devserver/`** - Local development server with ASGI adapter for uvicorn

### Key Components

1. **FunctionApp** - Main application class with FastAPI-style decorators
2. **create_function_service(*apps, registry=None)** - Creates composed handler from multiple apps with optional custom registry
3. **App Composition System**:
   - **Composition hook**: Apps override `on_compose()` to access routes, other apps, and shared registry
   - **Registry sharing**: Main app's dependency registry is shared with all composed apps
   - **Left-to-right routing**: Earlier apps in composition handle routes first
   - **Last-app metadata**: Uses final app for title/version in schemas
4. **SchemaGenerator** - Generates unified OpenAPI documentation across all apps
5. **Built-in Apps**:
   - **IntrospectionApp**: Provides `/__schema__`, `/__routes__`, `/__health__` endpoints
   - **MCPApp**: Provides `/__mcp_tools__`, `/__mcp_call__/*` endpoints
6. **Request Processing Pipeline**:
   - Parse request data and URL
   - Try each composed app in order (left-to-right evaluation)
   - Find matching route in current app
   - Validate and coerce parameters with recursive type conversion
   - Execute function with automatic error handling
   - Format response with structured success/error format

## Examples

The framework includes a complete example in `examples/handler.py` demonstrating:

- Type-safe routing with decorator syntax
- MCP integration for AI tool exposure
- Built-in introspection endpoints
- Async handler support
- Composable app architecture

## Limitations

- The framework does not support multiple body parameters. This may be supported in future versions.

## Development & Contributing

### Project Structure

```text
cognite-typed-functions/
├── src/
│   └── cognite_typed_functions/
│       ├── app.py              # Core FunctionApp class and decorators
│       ├── service.py          # Function service layer and app composition
│       ├── convert.py          # Type conversion and argument processing
│       ├── formatting.py       # Formatting utilities
│       ├── models.py           # Pydantic models and type definitions
│       ├── routing.py          # Route matching and management
│       ├── schema.py           # OpenAPI schema generation
│       ├── introspection.py    # Built-in introspection endpoints
│       ├── logger.py           # Enterprise logging utilities
│       ├── mcp.py              # Model Context Protocol integration
│       └── devserver/          # Local development server
│           ├── __init__.py     # Module exports
│           ├── asgi.py         # ASGI adapter for uvicorn
│           └── auth.py         # CogniteClient authentication
├── docs/
│   └── dev-server.md           # Local development guide
├── examples/
│   ├── handler.py              # Complete example with MCP integration
│   └── dev.py                  # Local dev server example
├── tests/                      # Comprehensive test suite
└── pyproject.toml              # Project configuration and dependencies
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run with coverage
uv run pytest --cov=cognite_typed_functions
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with appropriate tests
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.

## Acknowledgments

- Built specifically for [Cognite Data Fusion](https://www.cognite.com/) [Functions](https://docs.cognite.com/cdf/functions/) platform
- Decorator routing syntax inspired by [FastAPI](https://fastapi.tiangolo.com/)
- Data validation powered by [Pydantic](https://pydantic-docs.helpmanual.io/)
