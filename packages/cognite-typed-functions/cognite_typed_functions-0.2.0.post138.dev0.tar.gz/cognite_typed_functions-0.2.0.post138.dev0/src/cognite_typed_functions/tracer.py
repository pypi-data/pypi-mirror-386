"""Tracing support for Cognite Functions using dependency injection.

This module provides tracing capabilities through dependency injection,
making it available as a standard parameter like client, logger, etc.

Architecture:
- TracerProvider is configured once at application startup (not per-request)
- OTLPSpanExporter sends traces to OpenTelemetry collector (e.g., LightStep)
- BatchSpanProcessor handles async export without blocking requests
- No per-request setup/teardown to avoid resource leaks
- Spans include cognite.call_id attribute for filtering/organization in backend

Note:
    Tracing support requires the optional 'tracing' dependencies:
    pip install cognite-typed-functions[tracing]
"""

import inspect
import warnings
from collections.abc import Callable, Coroutine
from contextlib import contextmanager
from functools import wraps
from typing import TYPE_CHECKING, Any, ParamSpec, TypeVar, cast, overload

from cognite_typed_functions.app import FunctionApp
from cognite_typed_functions.dependency_registry import DependencyRegistry
from cognite_typed_functions.models import ASGIReceiveCallable, ASGISendCallable, ASGITypedFunctionScope, DataDict

# Try to import OpenTelemetry dependencies
_has_opentelemetry = True
try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider as SdkTracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExporter
    from opentelemetry.trace import ProxyTracerProvider, Status, StatusCode
except ImportError:
    _has_opentelemetry = False
    if not TYPE_CHECKING:
        # Provide stubs for runtime when OpenTelemetry is not installed
        trace = None  # type: ignore[assignment]
        OTLPSpanExporter = Any  # type: ignore[assignment]
        Resource = Any  # type: ignore[assignment]
        SdkTracerProvider = Any  # type: ignore[assignment]
        BatchSpanProcessor = Any  # type: ignore[assignment]
        SpanExporter = Any  # type: ignore[assignment]
        ProxyTracerProvider = Any  # type: ignore[assignment]
        Status = Any  # type: ignore[assignment]
        StatusCode = Any  # type: ignore[assignment]

if TYPE_CHECKING:
    # Always import for type checking
    from opentelemetry import trace as trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider as SdkTracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExporter
    from opentelemetry.trace import ProxyTracerProvider, Status, StatusCode

_P = ParamSpec("_P")
_R = TypeVar("_R")


class FunctionTracer:
    """Tracer for Cognite Functions with OpenTelemetry integration.

    Provides a simple interface for creating traced spans that are automatically
    exported to an OpenTelemetry collector (e.g., LightStep, Jaeger, etc.).
    """

    def __init__(self, tracer: "trace.Tracer") -> None:
        """Initialize the FunctionTracer.

        Args:
            tracer: OpenTelemetry Tracer instance

        Raises:
            ImportError: If OpenTelemetry is not installed
        """
        if not _has_opentelemetry:
            raise ImportError(
                "Tracing support requires OpenTelemetry. Install it with: pip install cognite-typed-functions[tracing]"
            )
        self.tracer = tracer

    @contextmanager
    def span(self, name: str):
        """Create a traced span.

        Usage:
            with tracer.span("database_query"):
                result = query_db()
        """
        with self.tracer.start_as_current_span(name) as span:
            # Explicitly set operation name as an attribute for better visibility in backends
            span.set_attribute("operation.name", name)
            try:
                yield span
                span.set_status(Status(StatusCode.OK))
            except Exception:
                # Re-raise to allow the OpenTelemetry context manager to handle it.
                # It will set the status to ERROR and record the exception with a stack trace.
                raise


# Overload: when exporter is provided
@overload
def setup_global_tracer_provider(
    *,
    service_name: str = "cognite-typed-functions",
    service_version: str = "1.0.0",
    exporter: "SpanExporter",
    insecure: bool = False,
) -> "trace.TracerProvider": ...


# Overload: when otlp_endpoint is required
@overload
def setup_global_tracer_provider(
    *,
    otlp_endpoint: str,
    service_name: str = "cognite-typed-functions",
    service_version: str = "1.0.0",
    insecure: bool = False,
) -> "trace.TracerProvider": ...


def setup_global_tracer_provider(
    *,
    otlp_endpoint: str | None = None,
    service_name: str = "cognite-typed-functions",
    service_version: str = "1.0.0",
    exporter: "SpanExporter | None" = None,
    insecure: bool = False,
) -> "trace.TracerProvider":
    """Set up global TracerProvider with OTLPSpanExporter.

    This is called once at application startup to configure OpenTelemetry
    for the lifetime of the function worker. Traces are sent to an OpenTelemetry
    collector (e.g., LightStep Developer Satellite) via OTLP/gRPC.

    This function is idempotent - calling it multiple times is safe and will
    return the existing provider if already configured.

    Args:
        otlp_endpoint: OTLP endpoint URL. Required when exporter is None.
        service_name: Service name for trace identification (default: "cognite-typed-functions")
        service_version: Service version (default: "1.0.0")
        exporter: Optional custom exporter (for testing). If not provided, uses OTLPSpanExporter.
        insecure: Use insecure connection (default: False). Only set to True for local development.

    Returns:
        The configured TracerProvider instance

    Raises:
        ImportError: If OpenTelemetry is not installed
        ValueError: If exporter is None but otlp_endpoint is not provided
    """
    if not _has_opentelemetry:
        raise ImportError(
            "Tracing support requires OpenTelemetry. Install it with: pip install cognite-typed-functions[tracing]"
        )

    # Validate that otlp_endpoint is provided when exporter is None
    if exporter is None and otlp_endpoint is None:
        raise ValueError("otlp_endpoint is required when exporter is not provided")

    # Check if already configured
    existing_provider = trace.get_tracer_provider()
    if not isinstance(existing_provider, ProxyTracerProvider):
        # Already configured, log a warning and return existing provider.
        warnings.warn("TracerProvider is already configured. Subsequent configurations will be ignored.")
        return existing_provider  # type: ignore[return-value]

    # Create resource with service identification (required by LightStep and other backends)
    # Using string literals for semantic convention keys to avoid deprecation warnings
    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": service_version,
        }
    )

    # Create and configure new provider with resource
    tracer_provider = SdkTracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)

    # Use provided exporter or create OTLP exporter
    if exporter is None:
        # otlp_endpoint is guaranteed to be non-None here due to validation above
        assert otlp_endpoint is not None  # For type checker
        exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=insecure)

    batch_processor = BatchSpanProcessor(exporter)
    tracer_provider.add_span_processor(batch_processor)

    return tracer_provider  # type: ignore[return-value]


class TracingApp(FunctionApp):
    """Tracing middleware app for automatic root span creation.

    Creates a root span around every incoming request at the middleware level,
    providing comprehensive tracing coverage including error handling. Routes
    decorated with @tracing.trace() create child spans under this root span.

    This app participates in the composition lifecycle but doesn't register
    any routes of its own - it wraps downstream apps in the middleware chain
    and provides tracer dependency injection.

    Example:
        tracing = TracingApp(otlp_endpoint="http://localhost:8360")

        @app.get("/items/{id}")
        @tracing.trace()  # Creates a child span
        def get_item(tracer: FunctionTracer, id: int):
            with tracer.span("business_logic"):  # Creates a grandchild span
                return {"id": id}

        # Compose with tracing app to enable tracing middleware
        handle = create_function_service(tracing, app)
    """

    # Parameter name for tracer dependency injection
    # This must match the DI registration for consistent behavior
    # Can be overridden in subclasses for custom naming conventions
    tracer_param_name: str = "tracer"

    def __init__(
        self,
        *,
        otlp_endpoint: str,
        service_name: str = "cognite-typed-functions",
        service_version: str = "1.0.0",
        insecure: bool = False,
    ) -> None:
        """Initialize the TracingApp.

        Sets up the global TracerProvider with OTLPSpanExporter
        for the lifetime of the application.

        Args:
            otlp_endpoint: OTLP endpoint URL (e.g., http://localhost:8360 for LightStep Satellite)
            service_name: Service name for trace identification (default: "cognite-typed-functions")
            service_version: Service version (default: "1.0.0")
            insecure: Use insecure connection (default: False). Only set to True for local development.

        Raises:
            ImportError: If OpenTelemetry is not installed
        """
        if not _has_opentelemetry:
            raise ImportError(
                "Tracing support requires OpenTelemetry. Install it with: pip install cognite-typed-functions[tracing]"
            )

        super().__init__(title="Tracing", version="1.0.0")

        # Use provided service name/version, or fall back to defaults
        # Note: We set title="Tracing" above, so we use a sensible default
        effective_service_name = service_name or "cognite-typed-functions"
        effective_service_version = service_version or "1.0.0"

        # Set up global tracer provider once at startup
        setup_global_tracer_provider(
            otlp_endpoint=otlp_endpoint,
            service_name=effective_service_name,
            service_version=effective_service_version,
            insecure=insecure,
        )

        # Get tracer for use in __call__
        self._tracer = trace.get_tracer(__name__)

    def on_compose(
        self,
        next_app: FunctionApp | None,
        shared_registry: DependencyRegistry,
    ) -> None:
        """Set the context for the TracingApp.

        Registers the FunctionTracer dependency in the shared registry.
        """
        # Set registry first (call parent implementation)
        super().on_compose(next_app, shared_registry)

        # Register the tracer dependency in the shared registry
        # The tracer uses the global TracerProvider that was set up in __init__
        if self.registry is None:
            raise ValueError("Registry is not set")

        self.registry.register(
            provider=lambda ctx: FunctionTracer(trace.get_tracer(__name__)),
            target_type=FunctionTracer,
            param_name=self.tracer_param_name,
            description="OpenTelemetry function tracer with OTLP export",
        )

    def _set_span_status_from_response(
        self,
        root_span: Any,
        response_state: dict[str, Any],
    ) -> None:
        """Set span status and attributes based on response state.

        Uses early returns to avoid nesting. Separates error detection
        logic from span annotation.

        Args:
            root_span: The OpenTelemetry span to annotate
            response_state: Response state dict with 'has_started' and 'body'
        """
        # No response sent - assume success
        if not response_state["has_started"]:
            root_span.set_attribute("http.status_code", 200)
            root_span.set_status(Status(StatusCode.OK))
            return

        response_body = response_state["body"]
        if not response_body:
            root_span.set_attribute("http.status_code", 200)
            root_span.set_status(Status(StatusCode.OK))
            return

        # Check if response indicates an error
        error_type = response_body.get("error_type")
        if not error_type:
            # Success response
            root_span.set_attribute("http.status_code", 200)
            root_span.set_status(Status(StatusCode.OK))
            return

        # Error response
        root_span.set_attribute("error", True)
        root_span.set_attribute("error.type", str(error_type))
        root_span.set_attribute("http.status_code", 500)
        error_message = response_body.get("message", "Error")
        root_span.set_status(Status(StatusCode.ERROR, str(error_message)))

    async def __call__(
        self,
        scope: ASGITypedFunctionScope,
        receive: ASGIReceiveCallable,
        send: ASGISendCallable,
    ) -> None:
        """ASGI interface with automatic root span creation.

        Creates a root span around the entire request lifecycle, including
        error handling. All downstream spans (from @trace() decorators or
        manual tracer.span() calls) will be children of this root span.

        Args:
            scope: ASGI scope containing request context
            receive: ASGI receive callable
            send: ASGI send callable
        """
        from opentelemetry.trace import SpanKind

        # Extract request metadata from scope
        request = scope.get("request")
        function_call_info = scope.get("function_call_info")

        # Determine span name from request
        if request:
            # Start with a low-cardinality name; will be updated with the route template later.
            span_name = request.method
        else:
            span_name = "cognite.function.request"

        # Create root span with SERVER kind for HTTP request handlers
        with self._tracer.start_as_current_span(span_name, kind=SpanKind.SERVER) as root_span:
            # Set HTTP and request attributes
            root_span.set_attribute("operation.name", span_name)
            if request:
                root_span.set_attribute("http.method", request.method)
                root_span.set_attribute("http.url", request.path)
                # Note: http.route will be set after routing completes by reading
                # from scope["state"]["matched_route_path"] (set by FunctionApp during dispatch)

            # Set Cognite-specific metadata if available (skip None values)
            if function_call_info:
                if function_id := function_call_info.get("function_id"):
                    root_span.set_attribute("cognite.function_id", function_id)
                if call_id := function_call_info.get("call_id"):
                    root_span.set_attribute("cognite.call_id", call_id)
                if schedule_id := function_call_info.get("schedule_id"):
                    root_span.set_attribute("cognite.schedule_id", schedule_id)
                if scheduled_time := function_call_info.get("scheduled_time"):
                    root_span.set_attribute("cognite.scheduled_time", scheduled_time)

            # Track response state - fail on multiple sends
            response_state: dict[str, Any] = {
                "has_started": False,
                "body": None,
            }

            # Wrap send to capture response
            async def wrapped_send(message: Any) -> None:
                match message:
                    case {"type": "cognite.function.response", "body": body} if isinstance(body, dict):
                        # Enforce single response rule
                        if response_state["has_started"]:
                            raise RuntimeError(
                                "Response has already been sent. "
                                "Multiple response sends are not allowed in the middleware chain."
                            )
                        response_state["has_started"] = True
                        response_state["body"] = cast(DataDict, body)
                    case _:
                        pass  # Other message types are forwarded without capturing

                await send(message)

            try:
                # Call parent which handles dispatch_request and next_app delegation
                await super().__call__(scope, receive, wrapped_send)

                # Update http.route with matched route template from scope state (if available)
                # This is set by FunctionApp after successful routing
                state = scope.get("state", {})
                if (matched_route_path := state.get("matched_route_path")) is not None:
                    root_span.set_attribute("http.route", matched_route_path)
                    if request:
                        root_span.update_name(f"{request.method} {matched_route_path}")

                # Set span status based on response
                self._set_span_status_from_response(root_span, response_state)

            except Exception:
                # Catch any unhandled exceptions (shouldn't happen with cognite_error_handler, but be defensive)
                # Re-raise to allow the OpenTelemetry context manager to handle it.
                # It will set the status to ERROR and record the exception with a stack trace.
                root_span.set_attribute("error", True)
                root_span.set_attribute("http.status_code", 500)
                raise

    def trace(self, span_name: str | None = None) -> Callable[[Callable[_P, _R]], Callable[_P, _R]]:
        """Decorator to create a child span with handler metadata.

        Creates a child span under the root span created by TracingApp.__call__.
        The child span includes function and route metadata for granular tracing.

        Note:
            The root span is automatically created at the middleware level by TracingApp.
            This decorator is optional and provides additional granularity for specific
            handlers that need detailed tracing.

        Args:
            span_name: Optional custom span name. If not provided, uses function name

        Returns:
            Decorator that wraps the function with a child span

        Example:
            @app.get("/items/{id}")
            @tracing.trace()  # Creates child span named "get_item"
            def get_item(tracer: FunctionTracer, id: int):
                with tracer.span("database_query"):  # Creates grandchild span
                    return {"id": id}

            @app.post("/items")
            @tracing.trace("create_item_operation")  # Custom span name
            def create_item(tracer: FunctionTracer, name: str):
                pass
        """

        def decorator(func: Callable[_P, _R]) -> Callable[_P, _R]:
            # Get route info from function metadata if set by @app.get/post decorators
            route_path = getattr(func, "_route_path", None)
            route_method = getattr(func, "_route_method", None)

            # Determine span name
            if span_name:
                effective_span_name = span_name
            else:
                effective_span_name = func.__name__

            # Check if function declares the tracer parameter
            # Uses strict name AND type matching to align with DI semantics
            sig = inspect.signature(func)
            param = sig.parameters.get(self.tracer_param_name)

            # Early exit if tracer parameter not declared with correct type
            if not param or param.annotation != FunctionTracer:
                return func

            def _update_root_span_with_route() -> None:
                """Update root span with route template for proper http.route semantics.

                Must be called before creating child span so get_current_span()
                returns the root span, not the child span.
                """
                if route_path and _has_opentelemetry:
                    root_span = trace.get_current_span()
                    if root_span and root_span.is_recording():
                        root_span.set_attribute("http.route", route_path)

            def _setup_span_attributes(child_span: Any) -> None:
                """Set up child span attributes with function-level metadata."""
                # Add operation name to child span
                child_span.set_attribute("operation.name", effective_span_name)

                # Add function metadata to child span
                child_span.set_attribute("function.name", func.__name__)

                # Add HTTP metadata to child span if available
                if route_path:
                    child_span.set_attribute("http.route", route_path)
                if route_method:
                    child_span.set_attribute("http.method", route_method)

            @wraps(func)
            def sync_wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                # Get tracer using configured parameter name
                tracer: FunctionTracer | None = cast(FunctionTracer | None, kwargs.get(self.tracer_param_name))

                if not tracer or not _has_opentelemetry:
                    # No tracer available or OpenTelemetry not installed, execute normally
                    return func(*args, **kwargs)

                # Update root span with route template before creating child span
                _update_root_span_with_route()

                # Create child span (inherits from root span created in __call__)
                with tracer.tracer.start_as_current_span(effective_span_name) as child_span:
                    _setup_span_attributes(child_span)
                    try:
                        result = func(*args, **kwargs)
                        child_span.set_status(Status(StatusCode.OK))
                        return result
                    except Exception:
                        # Re-raise to allow the OpenTelemetry context manager to handle it.
                        # It will set the status to ERROR and record the exception with a stack trace.
                        child_span.set_attribute("error", True)
                        raise

            @wraps(func)
            async def async_wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                # Get tracer using configured parameter name
                tracer: FunctionTracer | None = cast(FunctionTracer | None, kwargs.get(self.tracer_param_name))
                _func = cast(Callable[..., Coroutine[Any, Any, _R]], func)

                if not tracer or not _has_opentelemetry:
                    # No tracer available or OpenTelemetry not installed, execute normally
                    return await _func(*args, **kwargs)

                # Update root span with route template before creating child span
                _update_root_span_with_route()

                # Create child span (inherits from root span created in __call__)
                with tracer.tracer.start_as_current_span(effective_span_name) as child_span:
                    _setup_span_attributes(child_span)
                    try:
                        result = await _func(*args, **kwargs)
                        child_span.set_status(Status(StatusCode.OK))
                        return result
                    except Exception:
                        # Re-raise to allow the OpenTelemetry context manager to handle it.
                        # It will set the status to ERROR and record the exception with a stack trace.
                        child_span.set_attribute("error", True)
                        raise

            # Return appropriate wrapper based on function type
            if inspect.iscoroutinefunction(func):
                return async_wrapper  # type: ignore[return-value]
            else:
                return sync_wrapper  # type: ignore[return-value]

        return decorator


def create_tracing_app(
    *,
    otlp_endpoint: str,
    service_name: str = "cognite-typed-functions",
    service_version: str = "1.0.0",
    insecure: bool = False,
) -> TracingApp:
    """Create a TracingApp for decorator-based automatic root spans.

    Args:
        otlp_endpoint: OTLP endpoint URL (e.g., http://localhost:8360 for LightStep Satellite)
        service_name: Service name for trace identification (default: "cognite-typed-functions")
        service_version: Service version (default: "1.0.0")
        insecure: Use insecure connection (default: False). Only set to True for local development.

    Returns:
        TracingApp instance

    Example:
        from cognite_typed_functions.tracer import create_tracing_app

        # Secure connection (production, default)
        tracing = create_tracing_app(
            otlp_endpoint="https://ingest.lightstep.com:443",
            service_name="my-cognite-function",
            service_version="2.0.0"
        )

        # Insecure connection (local development only)
        tracing = create_tracing_app(
            otlp_endpoint="http://localhost:8360",
            service_name="my-cognite-function",
            service_version="2.0.0",
            insecure=True
        )

        @app.get("/items/{id}")
        @tracing.trace()
        def get_item(tracer: FunctionTracer, id: int):
            with tracer.span("database_query"):
                return {"id": id}
    """
    return TracingApp(
        otlp_endpoint=otlp_endpoint,
        service_name=service_name,
        service_version=service_version,
        insecure=insecure,
    )
