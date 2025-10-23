"""Base classes for OpenTelemetry instrumentors for GenAI libraries and tools.

This module defines the `BaseInstrumentor` abstract base class, which provides
common functionality and a standardized interface for instrumenting various
Generative AI (GenAI) libraries and Model Context Protocol (MCP) tools.
It includes methods for creating OpenTelemetry spans, recording metrics,
and handling configuration and cost calculation.
"""

import logging
import threading
import time
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional

import wrapt
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Status, StatusCode

from ..config import OTelConfig
from ..cost_calculator import CostCalculator

# Import semantic conventions
try:
    from openlit.semcov import SemanticConvention as SC
except ImportError:
    # Fallback if openlit not available
    class SC:
        GEN_AI_REQUESTS = "gen_ai.requests"
        GEN_AI_CLIENT_TOKEN_USAGE = "gen_ai.client.token.usage"
        GEN_AI_CLIENT_OPERATION_DURATION = "gen_ai.client.operation.duration"
        GEN_AI_USAGE_COST = "gen_ai.usage.cost"
        GEN_AI_SERVER_TTFT = "gen_ai.server.ttft"
        GEN_AI_SERVER_TBT = "gen_ai.server.tbt"


# Import histogram bucket definitions
try:
    from genai_otel.metrics import _GEN_AI_CLIENT_OPERATION_DURATION_BUCKETS
except ImportError:
    # Fallback buckets if import fails
    _GEN_AI_CLIENT_OPERATION_DURATION_BUCKETS = [
        0.01,
        0.02,
        0.04,
        0.08,
        0.16,
        0.32,
        0.64,
        1.28,
        2.56,
        5.12,
        10.24,
        20.48,
        40.96,
        81.92,
    ]

logger = logging.getLogger(__name__)
# Global flag to track if shared metrics have been created
_SHARED_METRICS_CREATED = False
_SHARED_METRICS_LOCK = threading.Lock()


class BaseInstrumentor(ABC):  # pylint: disable=R0902
    """Abstract base class for all LLM library instrumentors.

    Provides common functionality for setting up OpenTelemetry spans, metrics,
    and handling common instrumentation patterns.
    """

    # Class-level shared metrics (created once, shared by all instances)
    _shared_request_counter = None
    _shared_token_counter = None
    _shared_latency_histogram = None
    _shared_cost_counter = None
    _shared_error_counter = None
    # Streaming metrics (Phase 3.4)
    _shared_ttft_histogram = None
    _shared_tbt_histogram = None

    def __init__(self):
        """Initializes the instrumentor with OpenTelemetry tracers, meters, and common metrics."""
        self.tracer = trace.get_tracer(__name__)
        self.meter = metrics.get_meter(__name__)
        self.config: Optional[OTelConfig] = None
        self.cost_calculator = CostCalculator()
        self._instrumented = False

        # Use shared metrics to avoid duplicate warnings
        self._ensure_shared_metrics_created()

        # Reference the shared metrics
        self.request_counter = self._shared_request_counter
        self.token_counter = self._shared_token_counter
        self.latency_histogram = self._shared_latency_histogram
        self.cost_counter = self._shared_cost_counter
        self.error_counter = self._shared_error_counter
        # Streaming metrics
        self.ttft_histogram = self._shared_ttft_histogram
        self.tbt_histogram = self._shared_tbt_histogram

    @classmethod
    def _ensure_shared_metrics_created(cls):
        """Ensure shared metrics are created only once across all instrumentor instances."""
        global _SHARED_METRICS_CREATED

        with _SHARED_METRICS_LOCK:
            if _SHARED_METRICS_CREATED:
                return

            try:
                meter = metrics.get_meter(__name__)

                # Create shared metrics once using semantic conventions
                cls._shared_request_counter = meter.create_counter(
                    SC.GEN_AI_REQUESTS, description="Number of GenAI requests"
                )
                cls._shared_token_counter = meter.create_counter(
                    SC.GEN_AI_CLIENT_TOKEN_USAGE, description="Token usage for GenAI operations"
                )
                # Note: Histogram buckets should be configured via Views in MeterProvider
                # The advisory parameter is provided as a hint but Views take precedence
                cls._shared_latency_histogram = meter.create_histogram(
                    SC.GEN_AI_CLIENT_OPERATION_DURATION,
                    description="GenAI client operation duration",
                    unit="s",
                )
                cls._shared_cost_counter = meter.create_counter(
                    SC.GEN_AI_USAGE_COST, description="Cost of GenAI operations", unit="USD"
                )
                # Granular cost counters (Phase 3.2)
                cls._shared_prompt_cost_counter = meter.create_counter(
                    "gen_ai.usage.cost.prompt", description="Prompt tokens cost", unit="USD"
                )
                cls._shared_completion_cost_counter = meter.create_counter(
                    "gen_ai.usage.cost.completion", description="Completion tokens cost", unit="USD"
                )
                cls._shared_reasoning_cost_counter = meter.create_counter(
                    "gen_ai.usage.cost.reasoning",
                    description="Reasoning tokens cost (o1 models)",
                    unit="USD",
                )
                cls._shared_cache_read_cost_counter = meter.create_counter(
                    "gen_ai.usage.cost.cache_read",
                    description="Cache read cost (Anthropic)",
                    unit="USD",
                )
                cls._shared_cache_write_cost_counter = meter.create_counter(
                    "gen_ai.usage.cost.cache_write",
                    description="Cache write cost (Anthropic)",
                    unit="USD",
                )
                cls._shared_error_counter = meter.create_counter(
                    "gen_ai.client.errors", description="Number of GenAI client errors"
                )
                # Streaming metrics (Phase 3.4)
                # Note: Buckets should be configured via Views in MeterProvider
                cls._shared_ttft_histogram = meter.create_histogram(
                    SC.GEN_AI_SERVER_TTFT,
                    description="Time to first token in seconds",
                    unit="s",
                )
                cls._shared_tbt_histogram = meter.create_histogram(
                    SC.GEN_AI_SERVER_TBT,
                    description="Time between tokens in seconds",
                    unit="s",
                )

                _SHARED_METRICS_CREATED = True
                logger.debug("Shared metrics created successfully")

            except Exception as e:
                logger.error("Failed to create shared metrics: %s", e, exc_info=True)
                # Create dummy metrics that do nothing to avoid crashes
                cls._shared_request_counter = None
                cls._shared_token_counter = None
                cls._shared_latency_histogram = None
                cls._shared_cost_counter = None
                cls._shared_prompt_cost_counter = None
                cls._shared_completion_cost_counter = None
                cls._shared_reasoning_cost_counter = None
                cls._shared_cache_read_cost_counter = None
                cls._shared_cache_write_cost_counter = None
                cls._shared_error_counter = None
                cls._shared_ttft_histogram = None
                cls._shared_tbt_histogram = None

    @abstractmethod
    def instrument(self, config: OTelConfig):
        """Abstract method to implement library-specific instrumentation.

        Args:
            config (OTelConfig): The OpenTelemetry configuration object.
        """

    def create_span_wrapper(
        self, span_name: str, extract_attributes: Optional[Callable[[Any, Any, Any], Dict]] = None
    ) -> Callable:
        """Create a decorator that instruments a function with an OpenTelemetry span."""

        @wrapt.decorator
        def wrapper(wrapped, instance, args, kwargs):
            # If instrumentation failed during initialization, just call the original function.
            if not self._instrumented:
                logger.debug("Instrumentation not active, calling %s directly", span_name)
                return wrapped(*args, **kwargs)

            try:
                # Start a new span
                initial_attributes = {}
                if extract_attributes:
                    try:
                        extracted_attrs = extract_attributes(instance, args, kwargs)
                        for key, value in extracted_attrs.items():
                            if isinstance(value, (str, int, float, bool)):
                                initial_attributes[key] = value
                            else:
                                initial_attributes[key] = str(value)
                    except Exception as e:
                        logger.warning(
                            "Failed to extract attributes for span '%s': %s", span_name, e
                        )

                # Check if this is a streaming request before creating the span
                is_streaming = kwargs.get("stream", False)

                # Start the span (but don't use context manager for streaming to keep it open)
                span = self.tracer.start_span(span_name, attributes=initial_attributes)
                start_time = time.time()

                try:
                    # Call the original function
                    result = wrapped(*args, **kwargs)

                    if self.request_counter:
                        self.request_counter.add(1, {"operation": span.name})

                    # Handle streaming vs non-streaming responses (Phase 3.4)
                    if is_streaming:
                        # For streaming responses, wrap the iterator to capture TTFT/TBT
                        model = kwargs.get(
                            "model", initial_attributes.get("gen_ai.request.model", "unknown")
                        )
                        logger.debug(f"Detected streaming response for model: {model}")
                        # Wrap the streaming response - span will be finalized when iteration completes
                        return self._wrap_streaming_response(result, span, start_time, model)

                    # Non-streaming: record metrics and close span normally
                    try:
                        self._record_result_metrics(span, result, start_time, kwargs)
                    except Exception as e:
                        logger.warning("Failed to record metrics for span '%s': %s", span_name, e)

                    # Set span status to OK on successful execution
                    span.set_status(Status(StatusCode.OK))
                    span.end()
                    return result

                except Exception as e:
                    # Handle exceptions during the wrapped function execution
                    try:
                        if self.error_counter:
                            self.error_counter.add(
                                1, {"operation": span_name, "error_type": type(e).__name__}
                            )
                    except Exception:
                        pass

                    # Set span status to ERROR and record the exception
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    span.end()
                    raise

            except Exception as e:
                logger.error("Span creation failed for '%s': %s", span_name, e, exc_info=True)
                return wrapped(*args, **kwargs)

        return wrapper

    def _record_result_metrics(self, span, result, start_time: float, request_kwargs: dict = None):
        """Record metrics derived from the function result and execution time.

        Args:
            span: The OpenTelemetry span to record metrics on.
            result: The result from the wrapped function.
            start_time: The time when the function started executing.
            request_kwargs: The original request kwargs (for content capture).
        """
        # Record latency
        try:
            duration = time.time() - start_time
            if self.latency_histogram:
                self.latency_histogram.record(duration, {"operation": span.name})
        except Exception as e:
            logger.warning("Failed to record latency for span '%s': %s", span.name, e)

        # Extract and set response attributes if available
        try:
            if hasattr(self, "_extract_response_attributes"):
                response_attrs = self._extract_response_attributes(result)
                if response_attrs and isinstance(response_attrs, dict):
                    for key, value in response_attrs.items():
                        if isinstance(value, (str, int, float, bool)):
                            span.set_attribute(key, value)
                        elif isinstance(value, list):
                            # For arrays like finish_reasons
                            span.set_attribute(key, value)
                        else:
                            span.set_attribute(key, str(value))
        except Exception as e:
            logger.warning("Failed to extract response attributes for span '%s': %s", span.name, e)

        # Add content events if content capture is enabled
        try:
            if (
                hasattr(self, "_add_content_events")
                and self.config
                and self.config.enable_content_capture
            ):
                self._add_content_events(span, result, request_kwargs or {})
        except Exception as e:
            logger.warning("Failed to add content events for span '%s': %s", span.name, e)

        # Extract and record token usage and cost
        try:
            usage = self._extract_usage(result)
            if usage and isinstance(usage, dict):
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)
                total_tokens = usage.get("total_tokens", 0)

                # Record token counts if available and positive
                # Support dual emission based on OTEL_SEMCONV_STABILITY_OPT_IN
                emit_old_attrs = (
                    self.config
                    and self.config.semconv_stability_opt_in
                    and "dup" in self.config.semconv_stability_opt_in
                )

                if (
                    self.token_counter
                    and isinstance(prompt_tokens, (int, float))
                    and prompt_tokens > 0
                ):
                    self.token_counter.add(
                        prompt_tokens, {"token_type": "prompt", "operation": span.name}
                    )
                    # New semantic convention
                    span.set_attribute("gen_ai.usage.prompt_tokens", int(prompt_tokens))
                    # Old semantic convention (if dual emission enabled)
                    if emit_old_attrs:
                        span.set_attribute("gen_ai.usage.input_tokens", int(prompt_tokens))

                if (
                    self.token_counter
                    and isinstance(completion_tokens, (int, float))
                    and completion_tokens > 0
                ):
                    self.token_counter.add(
                        completion_tokens, {"token_type": "completion", "operation": span.name}
                    )
                    # New semantic convention
                    span.set_attribute("gen_ai.usage.completion_tokens", int(completion_tokens))
                    # Old semantic convention (if dual emission enabled)
                    if emit_old_attrs:
                        span.set_attribute("gen_ai.usage.output_tokens", int(completion_tokens))

                if isinstance(total_tokens, (int, float)) and total_tokens > 0:
                    span.set_attribute("gen_ai.usage.total_tokens", int(total_tokens))

                # Calculate and record cost if enabled and applicable
                if self.config and self.config.enable_cost_tracking and self._shared_cost_counter:
                    try:
                        model = span.attributes.get("gen_ai.request.model", "unknown")
                        # Assuming 'chat' as a default call_type for generic base instrumentor tests.
                        # Specific instrumentors will provide the actual call_type.
                        call_type = span.attributes.get("gen_ai.request.type", "chat")

                        # Use granular cost calculation for chat requests
                        if call_type == "chat":
                            costs = self.cost_calculator.calculate_granular_cost(
                                model, usage, call_type
                            )
                            total_cost = costs["total"]

                            # Record total cost
                            if total_cost > 0:
                                self._shared_cost_counter.add(total_cost, {"model": str(model)})
                                # Set span attributes for granular costs
                                span.set_attribute("gen_ai.usage.cost.total", total_cost)

                            # Record and set attributes for granular costs
                            if costs["prompt"] > 0 and self._shared_prompt_cost_counter:
                                self._shared_prompt_cost_counter.add(
                                    costs["prompt"], {"model": str(model)}
                                )
                                span.set_attribute("gen_ai.usage.cost.prompt", costs["prompt"])

                            if costs["completion"] > 0 and self._shared_completion_cost_counter:
                                self._shared_completion_cost_counter.add(
                                    costs["completion"], {"model": str(model)}
                                )
                                span.set_attribute(
                                    "gen_ai.usage.cost.completion", costs["completion"]
                                )

                            if costs["reasoning"] > 0 and self._shared_reasoning_cost_counter:
                                self._shared_reasoning_cost_counter.add(
                                    costs["reasoning"], {"model": str(model)}
                                )
                                span.set_attribute(
                                    "gen_ai.usage.cost.reasoning", costs["reasoning"]
                                )

                            if costs["cache_read"] > 0 and self._shared_cache_read_cost_counter:
                                self._shared_cache_read_cost_counter.add(
                                    costs["cache_read"], {"model": str(model)}
                                )
                                span.set_attribute(
                                    "gen_ai.usage.cost.cache_read", costs["cache_read"]
                                )

                            if costs["cache_write"] > 0 and self._shared_cache_write_cost_counter:
                                self._shared_cache_write_cost_counter.add(
                                    costs["cache_write"], {"model": str(model)}
                                )
                                span.set_attribute(
                                    "gen_ai.usage.cost.cache_write", costs["cache_write"]
                                )
                        else:
                            # For non-chat requests, use simple cost calculation
                            cost = self.cost_calculator.calculate_cost(model, usage, call_type)
                            if cost and cost > 0:
                                self._shared_cost_counter.add(cost, {"model": str(model)})
                    except Exception as e:
                        logger.warning("Failed to calculate cost for span '%s': %s", span.name, e)

        except Exception as e:
            logger.warning(
                "Failed to extract or record usage metrics for span '%s': %s", span.name, e
            )

    def _wrap_streaming_response(self, stream, span, start_time: float, model: str):
        """Wrap a streaming response to capture TTFT and TBT metrics.

        This generator wrapper yields chunks from the streaming response while
        measuring time to first token (TTFT) and time between tokens (TBT).
        The span is finalized when the stream completes or errors.

        Args:
            stream: The streaming response iterator
            span: The OpenTelemetry span for this request
            start_time: Request start time (for TTFT calculation)
            model: Model name/identifier for metric attributes

        Yields:
            Chunks from the original stream
        """
        from opentelemetry.trace import Status, StatusCode

        first_token = True
        last_token_time = start_time
        token_count = 0

        try:
            for chunk in stream:
                current_time = time.time()
                token_count += 1

                if first_token:
                    # Record Time to First Token
                    ttft = current_time - start_time
                    span.set_attribute("gen_ai.server.ttft", ttft)
                    if self.ttft_histogram:
                        self.ttft_histogram.record(ttft, {"model": model, "operation": span.name})
                    logger.debug(f"TTFT for {model}: {ttft:.3f}s")
                    first_token = False
                else:
                    # Record Time Between Tokens
                    tbt = current_time - last_token_time
                    if self.tbt_histogram:
                        self.tbt_histogram.record(tbt, {"model": model, "operation": span.name})

                last_token_time = current_time
                yield chunk

            # Stream completed successfully
            duration = time.time() - start_time
            if self.latency_histogram:
                self.latency_histogram.record(duration, {"operation": span.name})
            span.set_attribute("gen_ai.streaming.token_count", token_count)
            span.set_status(Status(StatusCode.OK))
            span.end()  # Close the span when streaming completes
            logger.debug(f"Streaming completed: {token_count} chunks in {duration:.3f}s")

        except Exception as e:
            # Stream failed
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            span.end()  # Close the span even on error
            if self.error_counter:
                self.error_counter.add(1, {"operation": span.name, "error_type": type(e).__name__})
            logger.warning(f"Error in streaming wrapper: {e}")
            raise

    @abstractmethod
    def _extract_usage(self, result) -> Optional[Dict[str, int]]:
        """Abstract method to extract token usage information from a function result.

        Subclasses must implement this to parse the specific library's response object
        and return a dictionary containing 'prompt_tokens', 'completion_tokens',
        and optionally 'total_tokens'.

        Args:
            result: The return value of the instrumented function.

        Returns:
            Optional[Dict[str, int]]: A dictionary with token counts, or None if usage cannot be extracted.
        """
