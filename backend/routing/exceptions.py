from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError, Throttled
from rest_framework.response import Response
from rest_framework import status
from .errors import (
    RoutingServiceError,
    GeocodingError,
    NoRouteFoundError,
    ProviderAuthError,
    ProviderRateLimitError,
    ProviderTimeoutError,
)


def custom_exception_handler(exc, context):
    """
    Standardized API exception handler to ensure a consistent error shape:
    {
        "error": {
            "code": "<error_code>",
            "message": "<human_readable_summary>",
            "details": { ... }
        }
    }
    """
    # 1. Domain Routing Exceptions
    if isinstance(exc, RoutingServiceError):
        if isinstance(exc, GeocodingError):
            status_code = status.HTTP_400_BAD_REQUEST
        elif isinstance(exc, NoRouteFoundError):
            status_code = status.HTTP_404_NOT_FOUND
        elif isinstance(exc, ProviderAuthError):
            status_code = status.HTTP_401_UNAUTHORIZED
        elif isinstance(exc, ProviderRateLimitError):
            status_code = status.HTTP_429_TOO_MANY_REQUESTS
        elif isinstance(exc, ProviderTimeoutError):
            status_code = status.HTTP_504_GATEWAY_TIMEOUT
        else:
            status_code = status.HTTP_502_BAD_GATEWAY

        return Response(
            {
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
            status=status_code,
        )

    # 2. DRF Built-in Exceptions
    response = exception_handler(exc, context)

    if response is not None:
        if isinstance(exc, ValidationError):
            code = "validation_error"
            message = "Invalid request payload or parameters."
            details = response.data
        elif isinstance(exc, Throttled):
            code = "request_throttled"
            wait_seconds = getattr(exc, 'wait', None)
            message = (
                f"Request was throttled. Expected available in {wait_seconds} seconds."
                if wait_seconds
                else "Request rate limit exceeded."
            )
            details = {"wait_seconds": wait_seconds}
        else:
            code = getattr(exc, 'default_code', 'api_error')
            message = str(exc.detail) if hasattr(exc, 'detail') else "An error occurred."
            details = response.data if isinstance(response.data, dict) else {"detail": response.data}

        response.data = {
            "error": {
                "code": code,
                "message": message,
                "details": details,
            }
        }

    return response
