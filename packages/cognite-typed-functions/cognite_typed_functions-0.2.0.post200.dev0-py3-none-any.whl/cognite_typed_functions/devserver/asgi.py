"""ASGI adapter for running Cognite Typed Functions locally with uvicorn.

This module provides the bridge between ASGI servers (like uvicorn) and the
Cognite Functions handle interface. It automatically includes interactive API
documentation endpoints (/docs, /openapi.json) for development.
"""

import json
import logging
import uuid
from collections.abc import Awaitable, Callable, MutableMapping, Sequence
from functools import wraps
from http import HTTPStatus
from typing import Any, Literal, TypedDict

from cognite.client import CogniteClient

from cognite_typed_functions.models import (
    ASGITypedFunctionRequestMessage,
    ASGITypedFunctionResponseMessage,
    ASGITypedFunctionScope,
    DataDict,
    FunctionCallInfo,
    HTTPMethod,
    RequestData,
)
from cognite_typed_functions.service import FunctionService

from .auth import get_cognite_client_from_env

logger = logging.getLogger(__name__)


# ASGI HTTP types
class ASGIHttpResponseStartMessage(TypedDict):
    """ASGI message."""

    type: Literal["http.response.start"]
    status: HTTPStatus
    headers: Sequence[tuple[bytes, bytes]]
    trailers: bool


class ASGIHttpResponseBodyMessage(TypedDict):
    """ASGI message."""

    type: Literal["http.response.body"]
    body: bytes
    more_body: bool


class ASGIHttpRequestMessage(TypedDict):
    """ASGI message."""

    type: Literal["http.request"]
    body: bytes
    more_body: bool


class ASGIHttpScope(TypedDict):
    """ASGI HTTP scope."""

    type: Literal["http"]
    method: HTTPMethod
    path: str
    query_string: bytes
    headers: Sequence[tuple[bytes, bytes]]
    client: tuple[str, int]
    server: tuple[str, int] | tuple[str, None]
    state: MutableMapping[str, Any]


ASGIReceive = Callable[[], Awaitable[ASGIHttpRequestMessage]]
ASGISend = Callable[[ASGIHttpResponseStartMessage | ASGIHttpResponseBodyMessage], Awaitable[None]]
ASGIApp = Callable[[ASGIHttpScope, ASGIReceive, ASGISend], Awaitable[None]]


def asgi_error_handler(
    func: Callable[[ASGIHttpScope, ASGIReceive, ASGISend], Awaitable[None]],
) -> Callable[[ASGIHttpScope, ASGIReceive, ASGISend], Awaitable[None]]:
    """Decorator that handles errors at the ASGI transport layer.

    Most error handling is done in the centralized cognite_error_handler in app.py.
    This ASGI-level handler provides defense-in-depth by catching:
    - JSONDecodeError during request body parsing (before calling handle)
    - Any unexpected exceptions that escape the core error handler (safety net)

    Args:
        func: The async ASGI application function to wrap

    Returns:
        Wrapped async ASGI application with error handling
    """

    @wraps(func)
    async def wrapper(scope: ASGIHttpScope, receive: ASGIReceive, send: ASGISend) -> None:
        try:
            await func(scope, receive, send)

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in request body: {e}")
            error_response: DataDict = {
                "success": False,
                "error_type": "InvalidJSON",
                "message": f"Invalid JSON in request body: {e!s}",
            }
            await _send_json_response(send, error_response, status=HTTPStatus.BAD_REQUEST)

        except Exception as e:
            # Safety net: This should normally not be reached since cognite_error_handler
            # in app.py catches all exceptions. However, if there's a bug in the error
            # handling code itself or an unexpected framework-level exception, this ensures
            # we still return a proper error response instead of crashing.
            logger.exception("Unhandled exception in ASGI app (this should not happen)")
            error_response = {
                "success": False,
                "error_type": "ServerError",
                "message": "An internal server error occurred.",
                "details": {"exception_type": type(e).__name__},
            }
            await _send_json_response(send, error_response, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    return wrapper


def create_synthetic_function_call_info(path: str) -> FunctionCallInfo:
    """Create synthetic function call info for local development.

    This enables tracing support in the dev server by providing the required
    Cognite metadata that would normally come from the Cognite Functions platform.

    Args:
        path: The HTTP request path

    Returns:
        Synthetic FunctionCallInfo with dev-server identifiers
    """
    # Generate a unique call_id for this request
    call_id = f"dev-{uuid.uuid4().hex[:16]}"

    return FunctionCallInfo(
        function_id="local-dev-server",
        call_id=call_id,
        schedule_id=None,
        scheduled_time=None,
    )


def create_asgi_app(handle: FunctionService) -> ASGIApp:
    """Create an ASGI application from a Cognite Functions handle.

    This adapter automatically includes interactive documentation endpoints:
    - /docs - Swagger UI interface
    - /openapi.json - Raw OpenAPI schema

    These documentation endpoints are only available in the development server
    and are not deployed to production Cognite Functions.

    Args:
        handle: The FunctionService instance created by create_function_service()

    Returns:
        ASGI application compatible with uvicorn, hypercorn, etc.

    Example:
        ```python
        from cognite_typed_functions import create_function_service
        from cognite_typed_functions.devserver import create_asgi_app

        handle = create_function_service(app)
        asgi_app = create_asgi_app(handle)
        ```

        Then run: `uv run uvicorn module:asgi_app --reload`
    """
    from .swagger import SwaggerMiddleware

    # Create Cognite client once at startup
    client = get_cognite_client_from_env()
    logger.info("🚀 ASGI app created successfully")
    logger.info("⚡ Using optimized async handle")
    logger.info("📚 Interactive docs available at /docs")

    @asgi_error_handler
    async def asgi_app(scope: ASGIHttpScope, receive: ASGIReceive, send: ASGISend) -> None:
        """ASGI application entry point.

        Args:
            scope: ASGI connection scope with request metadata
            receive: ASGI receive callable for reading request body
            send: ASGI send callable for writing response
        """
        if scope["type"] != "http":
            # Only handle HTTP requests
            return

        await _run_cognite_asgi_app(handle, scope, receive, send, client)

    # Compose with Swagger middleware using the compose pattern
    return SwaggerMiddleware(asgi_app, handle, client)


async def _run_cognite_asgi_app(
    handle: FunctionService,
    http_scope: ASGIHttpScope,
    http_receive: ASGIReceive,
    http_send: ASGISend,
    client: CogniteClient,
) -> None:
    """Run Cognite ASGI app by converting HTTP ASGI to Cognite ASGI format.

    Args:
        handle: FunctionService with ASGI app
        http_scope: HTTP ASGI scope
        http_receive: HTTP ASGI receive callable
        http_send: HTTP ASGI send callable
        client: Cognite client instance
    """
    # Parse HTTP request
    method = http_scope["method"]
    path = http_scope["path"]
    query_string = http_scope.get("query_string", b"").decode("utf-8")

    # Construct full path with query string
    full_path = path
    if query_string:
        full_path = f"{path}?{query_string}"

    # Read request body
    body_data: DataDict = {}
    if method in (HTTPMethod.POST, HTTPMethod.PUT, HTTPMethod.PATCH):
        body_bytes = await _read_body(http_receive)
        if body_bytes:
            # Let the caller handle any errors
            body_data = json.loads(body_bytes.decode("utf-8"))

    # Create RequestData
    request = RequestData(
        path=full_path,
        method=HTTPMethod(method),  # Convert string to HTTPMethod enum
        body=body_data,
    )

    # Build Typed Function ASGI scope
    # The state dict is shared by reference across all middleware layers
    state: dict[str, Any] = {}
    cognite_scope: ASGITypedFunctionScope = {
        "type": "cognite.function",
        "asgi": {"version": "3.0"},
        "client": client,
        "secrets": None,
        "function_call_info": create_synthetic_function_call_info(path),
        "request": request,
        "state": state,
    }

    # Response state - fail on multiple sends
    response_state: dict[str, Any] = {
        "has_started": False,
        "body": None,
    }

    async def cognite_receive() -> ASGITypedFunctionRequestMessage:
        return {
            "type": "cognite.function.request",
            "body": request,
        }

    async def cognite_send(message: ASGITypedFunctionResponseMessage) -> None:
        if message.get("type") == "cognite.function.response":
            body = message.get("body")
            # Enforce single response rule
            if response_state["has_started"]:
                raise RuntimeError(
                    "Response has already been sent. Multiple response sends are not allowed in the middleware chain."
                )
            response_state["has_started"] = True
            response_state["body"] = body

    # Run Cognite ASGI app directly
    if handle.asgi_app is not None:
        await handle.asgi_app(cognite_scope, cognite_receive, cognite_send)

    # Send HTTP response
    if not response_state["has_started"]:
        response_data = {
            "success": False,
            "error_type": "InternalError",
            "message": "ASGI app did not send response",
        }
    else:
        response_data = response_state["body"]

    await _send_json_response(http_send, response_data, status=HTTPStatus.OK)


async def _read_body(receive: ASGIReceive) -> bytes:
    """Read the complete request body from ASGI receive.

    Args:
        receive: ASGI receive callable

    Returns:
        Complete request body as bytes
    """
    body_parts: list[bytes] = []
    while True:
        message = await receive()
        if message["type"] == "http.request":
            body = message.get("body", b"")
            if body:
                body_parts.append(body)
            if not message.get("more_body", False):
                break
        elif message["type"] == "http.disconnect":
            # Client disconnected before sending the full body.
            break
    return b"".join(body_parts)


async def _send_json_response(send: ASGISend, data: DataDict, status: HTTPStatus = HTTPStatus.OK) -> None:
    """Send JSON response via ASGI send.

    Args:
        send: ASGI send callable
        data: Data to serialize as JSON
        status: HTTP status code
    """
    body = json.dumps(data).encode("utf-8")

    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode("utf-8")),
            ],
            "trailers": False,
        }
    )

    await send(
        {
            "type": "http.response.body",
            "body": body,
            "more_body": False,
        }
    )
