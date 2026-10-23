from typing import Any

from rest_framework import status
from rest_framework.exceptions import Throttled, ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

from .errors import (
    GeocodingError,
    NoRouteFoundError,
    ProviderAuthError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    RoutingServiceError,
)

ROUTING_EXCEPTION_STATUS_MAP = {
    GeocodingError: status.HTTP_400_BAD_REQUEST,
    NoRouteFoundError: status.HTTP_404_NOT_FOUND,
    ProviderAuthError: status.HTTP_401_UNAUTHORIZED,
    ProviderRateLimitError: status.HTTP_429_TOO_MANY_REQUESTS,
    ProviderTimeoutError: status.HTTP_504_GATEWAY_TIMEOUT,
}


def _handle_routing_error(routing_error: RoutingServiceError) -> Response:
    status_code = ROUTING_EXCEPTION_STATUS_MAP.get(type(routing_error), status.HTTP_502_BAD_GATEWAY)
    return Response(
        {
            "error": {
                "code": routing_error.code,
                "message": routing_error.message,
                "details": routing_error.details,
            }
        },
        status=status_code,
    )


def _extract_drf_error_envelope(framework_exception: Exception, raw_details: Any) -> dict:
    if isinstance(framework_exception, ValidationError):
        return {
            "code": "validation_error",
            "message": "Invalid request payload or parameters.",
            "details": raw_details,
        }
    if isinstance(framework_exception, Throttled):
        cooldown_seconds = getattr(framework_exception, "wait", None)
        throttle_message = (
            f"Request was throttled. Expected available in {cooldown_seconds} seconds."
            if cooldown_seconds
            else "Request rate limit exceeded."
        )
        return {
            "code": "request_throttled",
            "message": throttle_message,
            "details": {"wait_seconds": cooldown_seconds},
        }

    error_code = getattr(framework_exception, "default_code", "api_error")
    error_message = (
        str(framework_exception.detail)
        if hasattr(framework_exception, "detail")
        else "An error occurred."
    )
    structured_details = raw_details if isinstance(raw_details, dict) else {"detail": raw_details}
    return {
        "code": error_code,
        "message": error_message,
        "details": structured_details,
    }


def custom_exception_handler(active_exception: Exception, context: dict) -> Response:
    if isinstance(active_exception, RoutingServiceError):
        return _handle_routing_error(active_exception)

    standard_response = exception_handler(active_exception, context)
    if standard_response is not None:
        standard_response.data = {
            "error": _extract_drf_error_envelope(active_exception, standard_response.data)
        }
    return standard_response
