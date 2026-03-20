import requests
import time
import random
import logging
import sys
import os

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# -----------------
# TRACING CONFIG
# -----------------
resource = Resource(attributes={"service.name": "api-client"})
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer(__name__)

otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://jaeger:4317")
otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Automatically instrument the requests library so headers containing traceparent are injected
RequestsInstrumentor().instrument()

# -----------------
# LOGGING CONFIG
# -----------------
class TraceInjectingFormatter(logging.Formatter):
    def format(self, record):
        span = trace.get_current_span()
        trace_id = span.get_span_context().trace_id
        if trace_id == 0:
            record.trace_id = "0"
            record.span_id = "0"
        else:
            record.trace_id = format(trace_id, "032x")
            record.span_id = format(span.get_span_context().span_id, "016x")
        return super().format(record)

log_formatter = TraceInjectingFormatter('%(asctime)s - %(name)s - %(levelname)s - [trace_id=%(trace_id)s span_id=%(span_id)s] - %(message)s')
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(log_formatter)

file_handler = logging.FileHandler("client.log")
file_handler.setFormatter(log_formatter)

logger = logging.getLogger("api-client")
logger.setLevel(logging.DEBUG)
logger.addHandler(console_handler)
logger.addHandler(file_handler)

SERVER_URL = os.getenv("SERVER_URL", "http://localhost:5000")

def run_client():
    logger.info(f"Starting API client. Will continuously send requests to {SERVER_URL}")
    request_interval = 1.0
    
    while True:
        try:
            # Randomly pick an endpoint to send traffic to
            endpoint = random.choices(
                ['/', '/data', '/process', '/fake'], 
                weights=[0.1, 0.6, 0.2, 0.1]
            )[0]
            
            with tracer.start_as_current_span("client_request") as span:
                span.set_attribute("http.url", endpoint)
                logger.debug(f"Attempting to request {endpoint}")
            start_time = time.time()
            
            if endpoint == '/process':
                payload = {"key": "observability_test", "id": random.randint(1, 10000)}
                response = requests.post(f"{SERVER_URL}{endpoint}", json=payload, timeout=5)
            else:
                response = requests.get(f"{SERVER_URL}{endpoint}", timeout=5)
                
            elapsed = time.time() - start_time
            
            # Log based on the status code to generate meaningful logs for students
            if response.status_code == 200:
                logger.info(f"SUCCESS (200 OK) | Endpoint: {endpoint} | Latency: {elapsed:.2f}s")
            elif response.status_code >= 500:
                logger.error(f"SERVER ERROR ({response.status_code}) | Endpoint: {endpoint} | Response: {response.text}")
            elif response.status_code >= 400:
                logger.warning(f"CLIENT ERROR ({response.status_code}) | Endpoint: {endpoint} | Response: {response.text}")
            else:
                logger.info(f"UNEXPECTED STATUS ({response.status_code}) | Endpoint: {endpoint}")
                
        except requests.exceptions.Timeout:
            logger.error(f"TIMEOUT: Request to {SERVER_URL}{endpoint} timed out!")
        except requests.exceptions.ConnectionError:
            logger.critical(f"CONNECTION FAILED: Cannot reach the server at {SERVER_URL}. Is it down?")
        except Exception as e:
            logger.error(f"UNEXPECTED EXCEPTION: {e}")
            
        # Vary the load over time
        # This will create distinct request rate patterns in Prometheus
        if random.random() < 0.05:
            # Fluctuate the interval between 0.1 (high load) and 3.0 (low load)
            request_interval = random.uniform(0.1, 3.0)
            logger.debug(f"Adjusting request interval to {request_interval:.2f} seconds")
            
        time.sleep(request_interval)

if __name__ == '__main__':
    run_client()
