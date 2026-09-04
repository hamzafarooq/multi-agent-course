"""
OpenTelemetry setup for the customer support agent.
Sends traces to a local Arize Phoenix instance (http://localhost:6006).
No cloud credentials required.

Toggle with the TELEMETRY env var (default OFF):
    TELEMETRY=true   -> launch Phoenix, instrument google.genai, emit manual spans
    TELEMETRY=false  -> get_tracer() returns a no-op tracer; the heavy phoenix/otel
                        imports are never loaded, so nothing can slow down or crash a
                        run (e.g. a benchmark). Flip it on to demo observability live.

Server code should use `from telemetry import get_tracer, ATTR` and call
`tracer = get_tracer()` once at startup. It's idempotent and never raises.
"""

import os


def _phoenix_port() -> int:
    """Phoenix UI/OTLP port. s2s profile = 6007 (cascade uses 6006) so both apps can
    run their own Phoenix side by side."""
    return 6007


# --- Attribute keys (OpenInference semantic conventions) ---------------------
# Imported from openinference when available; otherwise a plain-string fallback so
# the servers can build spans without requiring the telemetry stack when disabled.
try:
    from openinference.semconv.trace import SpanAttributes as ATTR  # type: ignore
except Exception:  # pragma: no cover - fallback when openinference isn't installed
    class ATTR:  # noqa: N801 - mirror of openinference constant names
        OPENINFERENCE_SPAN_KIND = "openinference.span.kind"
        INPUT_VALUE = "input.value"
        OUTPUT_VALUE = "output.value"
        TOOL_NAME = "tool.name"
        LLM_TOKEN_COUNT_PROMPT = "llm.token_count.prompt"
        LLM_TOKEN_COUNT_COMPLETION = "llm.token_count.completion"
        LLM_TOKEN_COUNT_TOTAL = "llm.token_count.total"
        LLM_COST_PROMPT = "llm.cost.prompt"
        LLM_COST_COMPLETION = "llm.cost.completion"
        LLM_COST_TOTAL = "llm.cost.total"


# --- No-op tracer (used when TELEMETRY is off) -------------------------------
# Matches the tiny slice of the OTel tracer API the server code uses, so the same
# `with tracer.start_as_current_span(...) as span: span.set_attribute(...)` blocks
# work unchanged and cost effectively nothing when telemetry is disabled.
class _NoopSpan:
    def set_attribute(self, *a, **k):
        pass

    def record_exception(self, *a, **k):
        pass

    def set_status(self, *a, **k):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class _NoopTracer:
    def start_as_current_span(self, *a, **k):
        return _NoopSpan()


def telemetry_enabled() -> bool:
    """True when the TELEMETRY env var is set to a truthy value."""
    return os.getenv("TELEMETRY", "false").strip().lower() in ("1", "true", "yes", "on")


def init_telemetry():
    """Configure the OTLP exporter + Phoenix and return a real tracer.

    Heavy imports are done here (not at module load) so nothing is imported unless
    telemetry is actually turned on.
    """
    import webbrowser
    import phoenix as px
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from openinference.instrumentation.google_genai import GoogleGenAIInstrumentor

    # Each app runs its OWN Phoenix. Both the HTTP UI port AND the gRPC OTLP collector
    # port must be distinct, or the 2nd app crashes trying to bind the fixed gRPC 4317.
    # Derive gRPC from the UI port: cascade 6006->4317, s2s 6007->4318. Set via env
    # (the modern way — launch_app(port=) is deprecated).
    port = _phoenix_port()
    grpc_port = 4317 + (port - 6006)
    base = f"http://localhost:{port}"
    os.environ["PHOENIX_PORT"] = str(port)
    os.environ["PHOENIX_GRPC_PORT"] = str(grpc_port)
    try:
        px.launch_app()
    except Exception as exc:  # noqa: BLE001
        print(f"[telemetry] reusing the Phoenix already on :{port} (launch skipped: {exc})")

    exporter = OTLPSpanExporter(endpoint=f"{base}/v1/traces")
    provider = TracerProvider()
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    # Instruments every google.genai call — populates Phoenix input/output/tool columns.
    # This alone traces STT, the agent, TTS and the Live model in both text & voice.
    GoogleGenAIInstrumentor().instrument(tracer_provider=provider)

    # Tell ADK to capture message content in its own spans too
    os.environ.setdefault("OTEL_EXPORTER_OTLP_ENDPOINT", base)
    os.environ.setdefault("OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT", "true")

    # Pop the dashboard open so it's visible the moment the server starts.
    try:
        webbrowser.open(base)
    except Exception:  # noqa: BLE001 - headless / no browser is fine
        pass

    return trace.get_tracer("cs_agent")


_started = False
_tracer = None


def get_tracer():
    """Return a tracer: real (Phoenix/OTel) when TELEMETRY=true, else a no-op.

    Idempotent (safe to call from several modules) and never raises — telemetry must
    never block or crash the server.
    """
    global _started, _tracer
    if _started:
        return _tracer
    _started = True
    if telemetry_enabled():
        try:
            _tracer = init_telemetry()
            print(f"[telemetry] ENABLED -> Phoenix UI at http://localhost:{_phoenix_port()}")
        except Exception as exc:  # noqa: BLE001 - never let telemetry break the app
            print(f"[telemetry] init failed, continuing without it: {exc}")
            _tracer = _NoopTracer()
    else:
        _tracer = _NoopTracer()
    return _tracer
