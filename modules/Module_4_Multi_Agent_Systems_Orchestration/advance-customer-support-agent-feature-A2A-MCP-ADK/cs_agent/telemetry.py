"""
OpenTelemetry setup for the customer support agent.
Sends traces to a local Arize Phoenix instance (http://localhost:6006).
No cloud credentials required.
"""

import os
import phoenix as px
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from openinference.instrumentation.google_genai import GoogleGenAIInstrumentor

PHOENIX_OTLP_ENDPOINT = "http://localhost:6006/v1/traces"


def init_telemetry() -> trace.Tracer:
    """Configure OTLP exporter and return a tracer for manual spans."""
    px.launch_app()

    exporter = OTLPSpanExporter(endpoint=PHOENIX_OTLP_ENDPOINT)
    provider = TracerProvider()
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    # Instruments every google.genai call — populates Phoenix input/output/tool columns
    GoogleGenAIInstrumentor().instrument(tracer_provider=provider)

    # Tell ADK to capture message content in its own spans too
    os.environ.setdefault("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:6006")
    os.environ.setdefault("OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT", "true")

    return trace.get_tracer("cs_agent")
