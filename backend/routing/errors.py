"""
Custom domain exception hierarchy for routing, geocoding, and provider interactions.
"""


class RoutingServiceError(Exception):
    """Base class for routing domain exceptions."""

    def __init__(self, message: str, code: str = "routing_error", details: dict = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}


class GeocodingError(RoutingServiceError):
    """Raised when an address cannot be geocoded or resolved to valid coordinates."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message, code="geocoding_error", details=details)


class NoRouteFoundError(RoutingServiceError):
    """Raised when no drivable corridor connects the origin and destination."""

    def __init__(
        self,
        message: str = "No drivable route found between origin and destination.",
        details: dict = None,
    ):
        super().__init__(message, code="no_route_found", details=details)


class ProviderRateLimitError(RoutingServiceError):
    """Raised when the upstream provider returns a 429 rate limit exceeded response."""

    def __init__(
        self,
        message: str = "Upstream routing provider rate limit exceeded (429).",
        details: dict = None,
    ):
        super().__init__(message, code="provider_rate_limited", details=details)


class ProviderAuthError(RoutingServiceError):
    """Raised when upstream provider rejects credentials (401/403)."""

    def __init__(
        self,
        message: str = "Invalid or unauthorized routing provider API key.",
        details: dict = None,
    ):
        super().__init__(message, code="provider_auth_error", details=details)


class ProviderTimeoutError(RoutingServiceError):
    """Raised when an upstream provider call exceeds the configured timeout."""

    def __init__(self, message: str = "Routing provider request timed out.", details: dict = None):
        super().__init__(message, code="provider_timeout", details=details)


class ProviderSnappingError(RoutingServiceError):
    """Raised when a candidate via-waypoint cannot snap to the drivable network (ORS error 2010)."""

    def __init__(
        self,
        message: str = "Waypoint could not be snapped to the road network.",
        details: dict = None,
    ):
        super().__init__(message, code="waypoint_snapping_error", details=details)
