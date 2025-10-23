# src/agents_boot/observability/otel.py
import os

def init_otel(service_name: str = "novachain"):
    """
    Initialize OpenTelemetry if enabled and a collector endpoint is configured.
    - Enable by setting NOVACHAIN_OTEL=1 (or OTEL_EXPORTER_OTLP_ENDPOINT).
    - If not enabled, returns a no-op wrapper.
    """
    enabled = os.getenv("NOVACHAIN_OTEL") == "1" or bool(os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"))
    if not enabled:
        def instrument(app):  # no-op
            return app
        return instrument

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        provider = TracerProvider()
        exporter = OTLPSpanExporter()  # uses OTEL_EXPORTER_* envs
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)

        def instrument(app):
            FastAPIInstrumentor().instrument_app(app)
            return app

        return instrument
    except Exception:
        # On any failure, gracefully fall back to no-op
        def instrument(app):
            return app
        return instrument
