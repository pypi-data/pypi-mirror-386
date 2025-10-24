"""OpenTelemetry helpers for Vacasa Python services."""

from .otel import init_telemetry, OtelInitOptions

__version__ = "1.0.0"
__all__ = ["init_telemetry", "OtelInitOptions"]
