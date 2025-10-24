"""Middleware for FastAPI applications"""

import logging
from datetime import datetime
from multiprocessing.managers import dispatch
from uuid import uuid4

from opentelemetry.metrics import Meter
from opentelemetry.trace import StatusCode
from opentelemetry.trace import Tracer
from opentelemetry.util.http import parse_excluded_urls
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


try:
    from fastapi import FastAPI
    from fastapi import Request
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from secure import Secure
except ImportError as e:  # pragma: no cover
    logger.error(
        f"Dependencies missing. Is the 'fastapi' extra installed? e.g. pip install -U dkist-service-configuration[fastapi]: {e}"
    )  # pragma: no cover
    raise e  # pragma: no cover


__all__ = ["add_dkist_middleware", "instrument_fastapi_app"]


MAX_METRIC_NAME_LENGTH = 63


def instrument_fastapi_app(app: FastAPI, excluded_urls: str | None = None) -> None:

    FastAPIInstrumentor().instrument_app(app=app, excluded_urls=excluded_urls)


def _get_route_template(request: Request) -> str:
    """
    Return the FastAPI route template that matched this request, e.g. '/items/{item_id}'.
    Falls back to the raw path if routing info is missing (e.g. on 404).
    """
    route = request.scope.get("route")
    if route is not None and hasattr(route, "path"):
        template = route.path  # includes APIRouter prefixes (e.g. '/api/v1/items/{item_id}')
        root_path = request.scope.get("root_path", "") or ""
        if root_path:
            # ensure a single leading slash; avoid double slashes
            template = (root_path.rstrip("/") + template) or "/"
        return template
    # Fallback: raw URL path (still stable for static routes)
    return request.url.path


def add_dkist_middleware(
    app: FastAPI, tracer: Tracer, meter: Meter, excluded_urls: str | None = None
) -> None:
    """Add DKIST middleware to FastAPI application."""

    # parse the excluded URLs for instrumentation
    excluded_urls = parse_excluded_urls(excluded_urls)
    # Middleware to add security headers
    secure_headers = Secure()

    async def _add_security_headers(request: Request, call_next):
        response = await call_next(request)
        await secure_headers.set_headers_async(response)
        return response

    async def _add_tracking_headers(request: Request, call_next):
        """
        Middleware to add tracking headers to the response.
        """
        # start time of request evaluation
        request.state.start_time = datetime.now()
        # id used for correlating log entries
        request.state.conversation_id = uuid4().hex
        response = await call_next(request)
        # include conversation id in response for log correlation
        response.headers["X-Conversation-Id"] = request.state.conversation_id
        return response

    async def _trace_request(request: Request, call_next):
        """
        Middleware to trace requests and responses in FastAPI applications.
        """
        if excluded_urls and excluded_urls.url_disabled(str(request.url)):
            # if the URL is excluded from tracing, just process the request without tracing
            response = await call_next(request)
            return response

        with tracer.start_as_current_span("Process Request") as span:
            # annotate the span with request details
            span.set_attribute("conversation_id", request.state.conversation_id)
            span.set_attribute("http.request.method", request.method)
            span.set_attribute("http.request.url", str(request.url))
            span.set_attribute("dkist.root", "True")
            # process the request
            response = await call_next(request)
            span.set_status(StatusCode.OK)
            span.set_attribute("http.response.status_code", response.status_code)
        return response

    async def _meter_request(request: Request, call_next):
        """
        Middleware to increment meters around request processing.
        """
        # process the request first to get the response route
        response = await call_next(request)

        if excluded_urls and excluded_urls.url_disabled(str(request.url)):
            # if the URL is excluded from metrics, just process the request without tracing
            return response

        # total number of requests received
        request_counter = meter.create_up_down_counter(
            name=f"{meter.name}.rest.request.counter",
            unit="1",
            description="The number of requests received",
        )
        route_template = _get_route_template(request)
        attrs = {
            "http.request.method": request.method.upper(),
            "http.request.route": route_template,  # e.g. '/users/{user_id}'
            "http.request.target": request.url.path,
            "http.response.status_code": response.status_code,
        }
        request_counter.add(1, attributes=attrs)
        return response

    # Add middleware from innermost to outermost
    app.add_middleware(BaseHTTPMiddleware, dispatch=_trace_request)
    app.add_middleware(BaseHTTPMiddleware, dispatch=_add_security_headers)
    app.add_middleware(BaseHTTPMiddleware, dispatch=_add_tracking_headers)
    app.add_middleware(BaseHTTPMiddleware, dispatch=_meter_request)

    logger.info("DKIST middleware added to FastAPI application.")
