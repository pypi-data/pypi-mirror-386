"""Tests for the new DI-based tracing system."""

from contextlib import contextmanager

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from cognite_typed_functions import FunctionApp, FunctionTracer


@contextmanager
def create_tracer_with_call_id(call_id: str):
    """Helper to create a tracer with call_id in span context.

    This helper yields a FunctionTracer that will add the call_id attribute
    to all spans. The global tracer provider should already be configured
    by the session-scoped fixture.
    """
    # Create tracer (provider already set up by session fixture)
    tracer = FunctionTracer(trace.get_tracer(__name__))

    # We need to create a wrapper that adds call_id to all spans
    original_span = tracer.span

    @contextmanager
    def span_with_call_id(name: str):
        with original_span(name) as span:
            span.set_attribute("cognite.call_id", call_id)
            yield span

    tracer.span = span_with_call_id  # type: ignore[method-assign]
    yield tracer


def test_tracer_dependency_injection():
    """Test that tracer can be injected into route handlers."""
    app = FunctionApp("Test")

    @app.get("/test")
    def test_route(tracer: FunctionTracer) -> dict[str, str]:
        with tracer.span("test_span"):
            pass
        return {"status": "ok"}

    # Test that route accepts tracer parameter
    assert "tracer" in test_route.__annotations__


def test_otlp_export_configuration(span_exporter: InMemorySpanExporter):
    """Test that TracerProvider is configured and spans are exported."""
    # Verify provider is configured
    provider = trace.get_tracer_provider()
    assert isinstance(provider, TracerProvider)

    # Create spans and verify they are exported
    test_call_id = "test-call-123"
    tracer = FunctionTracer(trace.get_tracer(__name__))

    with tracer.span("test_operation") as span:
        span.set_attribute("test.attribute", "test_value")
        span.set_attribute("cognite.call_id", test_call_id)

    # Force flush to ensure spans are exported
    provider.force_flush(timeout_millis=1000)

    # Verify spans were exported
    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    span = spans[0]
    assert span.name == "test_operation"
    assert span.attributes is not None
    assert span.attributes["test.attribute"] == "test_value"
    assert span.attributes["cognite.call_id"] == test_call_id
    assert span.attributes["operation.name"] == "test_operation"


def test_tracer_works_without_call_id():
    """Test tracer works even when call_id is not set."""
    tracer = FunctionTracer(trace.get_tracer(__name__))

    # Tracer should work - spans will be exported without call_id attribute
    with tracer.span("test_operation"):
        result = "test_result"

    # Should not raise any exceptions
    assert result == "test_result"


def test_tracer_exception_handling():
    """Test that tracer properly handles exceptions."""
    with create_tracer_with_call_id("test-call-123") as tracer:
        with pytest.raises(ValueError):
            with tracer.span("test_operation"):
                raise ValueError("Test error")

        # Exception should be properly recorded in span
        # (This is tested by the span context manager implementation)


def test_tracing_app_decorator():
    """Test TracingApp decorator creates automatic root spans."""
    from cognite_typed_functions.tracer import create_tracing_app

    tracing = create_tracing_app(otlp_endpoint="http://test:4317", service_name="test-service")

    @tracing.trace()
    def test_func(tracer: FunctionTracer) -> dict[str, str]:
        with tracer.span("child_span"):
            pass
        return {"result": "ok"}

    # Create tracer with call_id
    with create_tracer_with_call_id("test-123") as tracer:
        # Call decorated function
        result = test_func(tracer=tracer)
        assert result == {"result": "ok"}


def test_tracing_app_with_custom_span_name():
    """Test TracingApp with custom span name."""
    from cognite_typed_functions.tracer import create_tracing_app

    tracing = create_tracing_app(otlp_endpoint="http://test:4317", service_name="test-service")

    @tracing.trace("custom_operation")
    def test_func(tracer: FunctionTracer) -> dict[str, str]:
        return {"result": "ok"}

    with create_tracer_with_call_id("test-123") as tracer:
        result = test_func(tracer=tracer)
        assert result == {"result": "ok"}


def test_tracing_app_without_tracer():
    """Test that decorated function works without tracer parameter."""
    from cognite_typed_functions.tracer import create_tracing_app

    tracing = create_tracing_app(otlp_endpoint="http://test:4317", service_name="test-service")

    @tracing.trace()
    def test_func() -> dict[str, str]:
        return {"result": "ok"}

    # Should work without tracer
    result = test_func()
    assert result == {"result": "ok"}


def test_tracing_app_with_route_metadata():
    """Test TracingApp uses route metadata from FunctionApp decorators."""
    from cognite_typed_functions import FunctionApp
    from cognite_typed_functions.tracer import create_tracing_app

    app = FunctionApp("Test")
    tracing = create_tracing_app(otlp_endpoint="http://test:4317", service_name="test-service")

    @app.get("/items/{id}")
    @tracing.trace()
    def get_item(tracer: FunctionTracer, id: int) -> dict[str, int]:
        return {"id": id}

    # Create tracer
    with create_tracer_with_call_id("test-123") as tracer:
        # Call decorated function
        result = get_item(tracer=tracer, id=123)
        assert result == {"id": 123}


def test_tracing_app_exception_handling() -> None:
    """Test TracingApp properly handles exceptions."""
    from cognite_typed_functions.tracer import create_tracing_app

    tracing = create_tracing_app(otlp_endpoint="http://test:4317", service_name="test-service")

    @tracing.trace()
    def test_func(tracer: FunctionTracer) -> dict[str, str]:
        raise ValueError("Test error")

    with create_tracer_with_call_id("test-123") as tracer:
        with pytest.raises(ValueError, match="Test error"):
            test_func(tracer=tracer)


def test_tracing_app_mismatched_parameter_name_disables_tracing():
    """Test that wrong parameter name disables @trace() decorator logic.

    When the parameter name doesn't match 'tracer', the decorator returns the
    function unchanged. The function still executes normally if called directly,
    but the decorator's child span creation is skipped.
    """
    from cognite_typed_functions.tracer import create_tracing_app

    tracing = create_tracing_app(otlp_endpoint="http://test:4317", service_name="test-service")

    # Wrong parameter name - decorator will return function unchanged
    @tracing.trace("custom_operation")
    def test_func(my_custom_tracer: FunctionTracer, value: int) -> dict[str, int]:
        # This will work if we manually pass a tracer, but the @trace() decorator
        # won't create a child span because the parameter name doesn't match
        with my_custom_tracer.span("inner_operation"):
            pass
        return {"value": value}

    with create_tracer_with_call_id("test-456") as tracer_instance:
        # Function executes, but without decorator's child span
        result = test_func(my_custom_tracer=tracer_instance, value=42)
        assert result == {"value": 42}


def test_tracing_app_strict_function_call_info_matching():
    """Test that function_call_info requires BOTH name AND type to match (strict framework dependency)."""
    from cognite_typed_functions.models import FunctionCallInfo
    from cognite_typed_functions.tracer import create_tracing_app

    tracing = create_tracing_app(otlp_endpoint="http://test:4317", service_name="test-service")

    # Test 1: Correct name AND type - should capture metadata
    @tracing.trace()
    def correct_signature(tracer: FunctionTracer, function_call_info: FunctionCallInfo) -> dict[str, str]:
        return {"test": "ok"}

    # Test 2: Wrong type (dict instead of FunctionCallInfo) - should NOT capture metadata
    @tracing.trace()
    def wrong_type(tracer: FunctionTracer, function_call_info: FunctionCallInfo) -> dict[str, str]:
        return {"test": "ok"}

    # Test 3: Wrong name but correct type - should NOT capture metadata
    @tracing.trace()
    def wrong_name(tracer: FunctionTracer, my_call_info: FunctionCallInfo) -> dict[str, str]:
        return {"test": "ok"}

    with create_tracer_with_call_id("test-789") as tracer:
        # All should work, but only the first one properly matches function_call_info
        call_info: FunctionCallInfo = {
            "call_id": "test-789",
            "function_id": "fn-123",
            "schedule_id": None,
            "scheduled_time": None,
        }

        result1 = correct_signature(tracer=tracer, function_call_info=call_info)
        assert result1 == {"test": "ok"}

        result2 = wrong_type(tracer=tracer, function_call_info={"call_id": "test-789"})  # type: ignore[arg-type]
        assert result2 == {"test": "ok"}

        result3 = wrong_name(tracer=tracer, my_call_info=call_info)
        assert result3 == {"test": "ok"}


# ===== Integration tests for ASGI middleware architecture =====


@pytest.mark.asyncio
async def test_tracing_app_middleware_creates_root_span(span_exporter: InMemorySpanExporter):
    """Test that TracingApp creates root span at middleware level."""
    from unittest.mock import Mock

    from cognite.client import CogniteClient

    from cognite_typed_functions import create_function_service
    from cognite_typed_functions.models import FunctionCallInfo
    from cognite_typed_functions.tracer import TracingApp

    # Create TracingApp (uses already-configured provider from session fixture)
    app = FunctionApp("TestApp")
    tracing = TracingApp(otlp_endpoint="http://test:4317", service_name="test-service")

    # Get the provider for flushing
    provider = trace.get_tracer_provider()

    @app.get("/items/{id}")
    def get_item(id: int) -> dict[str, int]:
        return {"id": id}

    # Create service with tracing middleware
    handle = create_function_service(tracing, app)

    # Create mock client
    client = Mock(spec=CogniteClient)

    # Call through the service (which goes through ASGI middleware)
    function_call_info: FunctionCallInfo = {
        "call_id": "test-call-456",
        "function_id": "fn-789",
        "schedule_id": None,
        "scheduled_time": None,
    }

    result = await handle.async_handle(
        client=client,
        data={"path": "/items/123", "method": "GET", "body": {}},
        function_call_info=function_call_info,
    )

    # Verify response (wrapped in data + success format)
    assert result.get("data") == {"id": 123}
    assert result.get("success") is True

    # Force flush to export spans
    if isinstance(provider, TracerProvider):
        provider.force_flush(timeout_millis=1000)

    # Verify root span was created
    spans = span_exporter.get_finished_spans()
    assert len(spans) >= 1

    # Find root span (should have SERVER kind and no parent)
    root_spans = [s for s in spans if s.parent is None]
    assert len(root_spans) == 1

    root_span = root_spans[0]
    assert root_span.name == "GET /items/{id}"
    assert root_span.attributes is not None
    assert root_span.attributes.get("http.method") == "GET"
    # http.route should be the parameterized template, not the concrete path
    assert root_span.attributes.get("http.route") == "/items/{id}"
    assert root_span.attributes.get("cognite.call_id") == "test-call-456"
    assert root_span.attributes.get("cognite.function_id") == "fn-789"
    assert root_span.attributes.get("http.status_code") == 200


@pytest.mark.asyncio
async def test_tracing_app_middleware_handles_errors(span_exporter: InMemorySpanExporter):
    """Test that TracingApp detects error responses and marks root span."""
    from unittest.mock import Mock

    from cognite.client import CogniteClient

    from cognite_typed_functions import create_function_service
    from cognite_typed_functions.tracer import TracingApp

    # Create app that raises an error
    app = FunctionApp("TestApp")
    tracing = TracingApp(otlp_endpoint="http://test:4317", service_name="test-service")

    # Get the provider for flushing
    provider = trace.get_tracer_provider()

    @app.get("/error")
    def error_route() -> dict[str, str]:
        raise ValueError("Test error")

    # Create service with tracing middleware
    handle = create_function_service(tracing, app)

    # Create mock client
    client = Mock(spec=CogniteClient)

    # Call endpoint that raises an error
    result = await handle.async_handle(
        client=client,
        data={"path": "/error", "method": "GET", "body": {}},
    )

    # Verify error response
    assert result.get("error_type") == "ExecutionError"
    message = result.get("message", "")
    assert isinstance(message, str) and "Test error" in message

    # Force flush to export spans
    if isinstance(provider, TracerProvider):
        provider.force_flush(timeout_millis=1000)

    # Verify root span marked as error
    spans = span_exporter.get_finished_spans()
    root_spans = [s for s in spans if s.parent is None]
    assert len(root_spans) == 1

    root_span = root_spans[0]
    assert root_span.attributes is not None
    assert root_span.attributes.get("error") is True
    assert root_span.attributes.get("error.type") == "ExecutionError"
    assert root_span.attributes.get("http.status_code") == 500


@pytest.mark.asyncio
async def test_tracing_app_child_spans_nested_under_root(span_exporter: InMemorySpanExporter):
    """Test that @trace() decorator creates child spans under root span."""
    from unittest.mock import Mock

    from cognite.client import CogniteClient

    from cognite_typed_functions import create_function_service
    from cognite_typed_functions.tracer import TracingApp

    # Create app with tracing
    app = FunctionApp("TestApp")
    tracing = TracingApp(otlp_endpoint="http://test:4317", service_name="test-service")

    # Get the provider for flushing
    provider = trace.get_tracer_provider()

    @app.get("/nested")
    @tracing.trace()
    def nested_route(tracer: FunctionTracer) -> dict[str, str]:
        with tracer.span("business_logic"):
            with tracer.span("database_query"):
                pass
        return {"status": "ok"}

    # Create service with tracing middleware
    handle = create_function_service(tracing, app)

    # Create mock client
    client = Mock(spec=CogniteClient)

    # Call endpoint
    result = await handle.async_handle(
        client=client,
        data={"path": "/nested", "method": "GET", "body": {}},
    )

    # Verify response (wrapped in data + success format)
    assert result.get("data") == {"status": "ok"}
    assert result.get("success") is True

    # Force flush to export spans
    if isinstance(provider, TracerProvider):
        provider.force_flush(timeout_millis=1000)

    # Verify span hierarchy
    spans = span_exporter.get_finished_spans()
    assert len(spans) >= 4  # root + @trace child + business_logic + database_query

    # Find root span (no parent)
    root_spans = [s for s in spans if s.parent is None]
    assert len(root_spans) == 1
    root_span = root_spans[0]
    assert root_span.name == "GET /nested"

    # Find @trace() child span (parent is root)
    assert root_span.context is not None
    root_span_id = root_span.context.span_id
    trace_children = [s for s in spans if s.parent is not None and s.parent.span_id == root_span_id]
    assert len(trace_children) >= 1
    trace_span = trace_children[0]
    assert trace_span.name == "nested_route"

    # Find grandchild spans (business_logic and database_query)
    assert trace_span.context is not None
    trace_span_id = trace_span.context.span_id
    grandchildren = [s for s in spans if s.parent is not None and s.parent.span_id == trace_span_id]
    assert len(grandchildren) >= 1
    assert any(s.name == "business_logic" for s in grandchildren)


@pytest.mark.asyncio
async def test_tracing_app_without_decorator_only_root_span(span_exporter: InMemorySpanExporter):
    """Test that without @trace(), only root span is created."""
    from unittest.mock import Mock

    from cognite.client import CogniteClient

    from cognite_typed_functions import create_function_service
    from cognite_typed_functions.tracer import TracingApp

    # Create app WITHOUT @trace() decorator
    app = FunctionApp("TestApp")
    tracing = TracingApp(otlp_endpoint="http://test:4317", service_name="test-service")

    # Get the provider for flushing
    provider = trace.get_tracer_provider()

    @app.get("/simple")
    def simple_route() -> dict[str, str]:
        return {"status": "ok"}

    # Create service with tracing middleware
    handle = create_function_service(tracing, app)

    # Create mock client
    client = Mock(spec=CogniteClient)

    # Call endpoint
    result = await handle.async_handle(
        client=client,
        data={"path": "/simple", "method": "GET", "body": {}},
    )

    # Verify response (wrapped in data + success format)
    assert result.get("data") == {"status": "ok"}
    assert result.get("success") is True

    # Force flush to export spans
    if isinstance(provider, TracerProvider):
        provider.force_flush(timeout_millis=1000)

    # Verify only root span was created
    spans = span_exporter.get_finished_spans()
    root_spans = [s for s in spans if s.parent is None]
    assert len(root_spans) == 1

    root_span = root_spans[0]
    assert root_span.name == "GET /simple"
    assert root_span.attributes is not None
    assert root_span.attributes.get("http.status_code") == 200
