"""OpenTelemetry initialization for Python services."""

import atexit
import logging
import os
import signal
from dataclasses import dataclass, field
from typing import Dict, Optional, Any

from opentelemetry import trace, metrics
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.semconv.resource import ResourceAttributes

DEFAULT_SERVICE_NAME = "vacasa-python-service"

DEFAULT_TRACE_PATH = "/v1/traces"
DEFAULT_LOGS_PATH = "/v1/logs"
DEFAULT_METRICS_PATH = "/v1/metrics"
DEFAULT_METRIC_INTERVAL = 5000  # milliseconds
DEFAULT_LOG_TIMEOUT = 3000  # milliseconds

logger = logging.getLogger(__name__)

_sdk_initialized = False
_tracer_provider: Optional[TracerProvider] = None
_meter_provider: Optional[MeterProvider] = None
_logger_provider: Optional[LoggerProvider] = None
_shutdown_hook_registered = False


@dataclass
class OtelInitOptions:
    """Configuration options for OpenTelemetry initialization."""
    
    service_name: Optional[str] = None
    metric_export_interval_millis: int = DEFAULT_METRIC_INTERVAL
    log_export_timeout_millis: int = DEFAULT_LOG_TIMEOUT
    tags: Dict[str, Any] = field(default_factory=dict)
    debug: bool = False
    sampling_rate: Optional[float] = None
    log_injection: bool = True


def _register_shutdown_hook() -> None:
    """Register shutdown handlers for graceful cleanup."""
    global _shutdown_hook_registered
    
    if _shutdown_hook_registered:
        return
    
    def shutdown_handler(signum=None, frame=None):
        """Shutdown all OpenTelemetry providers."""
        try:
            if _tracer_provider:
                _tracer_provider.shutdown()
            if _meter_provider:
                _meter_provider.shutdown()
            if _logger_provider:
                _logger_provider.shutdown()
        except Exception as e:
            logger.error(f"Error during OpenTelemetry shutdown: {e}")
        finally:
            if signum is not None:
                os._exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)
    
    # Register atexit handler for normal termination
    atexit.register(shutdown_handler)
    
    _shutdown_hook_registered = True


def _create_sdk(options: OtelInitOptions) -> None:
    """Create and configure OpenTelemetry SDK components."""
    global _tracer_provider, _meter_provider, _logger_provider
    
    if options.debug:
        logging.basicConfig(level=logging.DEBUG)
        logger.setLevel(logging.DEBUG)
    
    apm_enabled = os.getenv("OTEL_APM_ENABLED", "").strip().lower() == "true"
    
    service_name = (
        options.service_name 
        or os.getenv("OTEL_SERVICE_NAME") 
        or DEFAULT_SERVICE_NAME
    )
    
    otel_host_collector = os.getenv("OTEL_HOST_COLLECTOR", "")
    
    trace_endpoint = f"{otel_host_collector}{DEFAULT_TRACE_PATH}"
    logs_endpoint = f"{otel_host_collector}{DEFAULT_LOGS_PATH}"
    metrics_endpoint = f"{otel_host_collector}{DEFAULT_METRICS_PATH}"
    
    metric_interval = options.metric_export_interval_millis / 1000  # Convert to seconds
    log_timeout = options.log_export_timeout_millis / 1000  # Convert to seconds
    
    # Build resource attributes
    resource_attributes = {
        ResourceAttributes.SERVICE_NAME: service_name,
        **options.tags,
    }
    
    resource = Resource.create(resource_attributes)
    
    logger.debug(
        f"OpenTelemetry configuration: host={otel_host_collector}, "
        f"service={service_name}, apm={apm_enabled}"
    )
    
    # Configure sampling rate
    sampling_rate = options.sampling_rate
    if sampling_rate is None:
        sampling_rate = 0.5 if apm_enabled else 0.0
    
    # Create Tracer Provider
    sampler = TraceIdRatioBased(sampling_rate)
    _tracer_provider = TracerProvider(resource=resource, sampler=sampler)
    
    trace_exporter = OTLPSpanExporter(endpoint=trace_endpoint)
    _tracer_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
    
    trace.set_tracer_provider(_tracer_provider)
    
    # Create Meter Provider
    metric_reader = PeriodicExportingMetricReader(
        exporter=OTLPMetricExporter(endpoint=metrics_endpoint),
        export_interval_millis=int(metric_interval * 1000)
    )
    _meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(_meter_provider)
    
    # Create Logger Provider
    log_exporter = OTLPLogExporter(endpoint=logs_endpoint)
    _logger_provider = LoggerProvider(resource=resource)
    _logger_provider.add_log_record_processor(
        BatchLogRecordProcessor(log_exporter, export_timeout_millis=int(log_timeout * 1000))
    )
    
    # Setup log injection if enabled
    if options.log_injection:
        handler = LoggingHandler(level=logging.INFO, logger_provider=_logger_provider)
        logging.getLogger().addHandler(handler)
        
        # Instrument the logging module
        LoggingInstrumentor().instrument(set_logging_format=True)
    
    logger.debug("OpenTelemetry SDK started")


def init_telemetry(options: Optional[OtelInitOptions] = None) -> None:
    """
    Initialize OpenTelemetry for the application.
    
    Args:
        options: Configuration options for OpenTelemetry initialization.
                If None, uses default options.
    
    Environment Variables:
        OTEL_HOST_COLLECTOR: The OpenTelemetry collector endpoint (required)
        OTEL_SERVICE_NAME: Service name for telemetry data
        OTEL_APM_ENABLED: Enable full APM instrumentation ("true" or "false")
    
    Example:
        >>> from vacasa_opentelemetry import init_telemetry, OtelInitOptions
        >>> 
        >>> init_telemetry(OtelInitOptions(
        ...     service_name="my-service",
        ...     debug=True,
        ...     tags={"environment": "production"}
        ... ))
    """
    global _sdk_initialized
    
    if options is None:
        options = OtelInitOptions()
    
    otel_host_collector = os.getenv("OTEL_HOST_COLLECTOR")
    if not otel_host_collector:
        logger.info(
            "OTEL_HOST_COLLECTOR env var not set, skipping OpenTelemetry initialization"
        )
        return
    
    if _sdk_initialized:
        logger.debug("OpenTelemetry already initialized, skipping")
        return
    
    _create_sdk(options)
    _register_shutdown_hook()
    _sdk_initialized = True
