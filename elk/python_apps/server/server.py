import time
import random
import logging
import threading
import sys
import os
from flask import Flask, request, jsonify
from prometheus_flask_exporter import PrometheusMetrics
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# -----------------
# TRACING CONFIG
# -----------------
resource = Resource(attributes={"service.name": "api-server"})
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer(__name__)

# OTLP Exporter pointing to Jaeger
otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://jaeger:4317")
otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

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

file_handler = logging.FileHandler("server.log")
file_handler.setFormatter(log_formatter)

logger = logging.getLogger("api-server")
logger.setLevel(logging.DEBUG)
logger.addHandler(console_handler)
logger.addHandler(file_handler)

app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)

# -----------------
# METRICS CONFIG
# -----------------
# This automatically exposes a /metrics endpoint and tracks requests.
metrics = PrometheusMetrics(app)

# Static information as metric
metrics.info('app_info', 'Application info', version='1.0.0')

def crash_simulator():
    """
    Background thread that randomly crashes the server.
    This simulates incidents like High CPU, RAM full, or sudden process death,
    forcing students to analyze the logs/metrics and react.
    """
    logger.info("Crash simulator initialized. Server will experience an incident later.")
    # Wait between 2 minutes and 10 minutes before an incident
    wait_time = random.randint(120, 600)
    time.sleep(wait_time)
    
    incidents = ['cpu_spike', 'memory_leak', 'sudden_crash']
    incident = random.choice(incidents)
    
    logger.critical(f"INCIDENT INITIATED: {incident.upper()} DETECTED!")
    
    if incident == 'cpu_spike':
        logger.error("SYSTEM ALERT: CPU load reaching 100%. System becoming unresponsive.")
        # Simulating 100% CPU on this thread
        while True:
            pass
            
    elif incident == 'memory_leak':
        logger.error("SYSTEM ALERT: Out of memory. Rapid consumption detected.")
        leak_array = []
        try:
            while True:
                # Appending large blocks of strings to fill RAM
                leak_array.append(" " * (10 ** 7)) # ~10MB per iteration
                time.sleep(0.05) # Ramp up memory fast
        except MemoryError:
            logger.critical("SYSTEM ALERT: MemoryError raised! Crashing process.")
            os._exit(1)
            
    elif incident == 'sudden_crash':
        logger.fatal("SYSTEM ALERT: Fatal Segmentation Fault or Kernel Panic. Process dying.")
        os._exit(1)

@app.route('/')
def index():
    logger.info("Accessing root endpoint")
    return jsonify({"status": "running", "message": "Welcome to the Observability Lab API"})

@app.route('/data')
def get_data():
    logger.debug("Received request on /data endpoint")
    
    # Simulate random latency
    if random.random() < 0.2:
        sleep_time = random.uniform(0.5, 3.0)
        logger.warning(f"Simulating high latency: Request will take {sleep_time:.2f}s")
        time.sleep(sleep_time)
        
    # Simulate random 500 internal server errors
    if random.random() < 0.1:
        logger.error("Failed to fetch data from the mock database. Database connection timeout.")
        return jsonify({"error": "Database connection failed", "details": "Timeout"}), 500
        
    logger.info("Successfully fetched mock data.")
    return jsonify({"data": [1, 2, 3, 4, 5], "count": 5})

@app.route('/process', methods=['POST'])
def process_data():
    logger.debug("Received POST request on /process endpoint")
    payload = request.json
    
    if not payload:
        logger.warning("Received an empty POST payload.")
        return jsonify({"error": "No payload provided"}), 400
        
    logger.info(f"Processing payload of size {len(str(payload))}")
    time.sleep(random.uniform(0.1, 0.5)) # Small processing time
    
    # Randomly fail the processing
    if random.random() < 0.05:
        logger.error("Data processing failed due to internal validation error.")
        return jsonify({"error": "Validation failed on payload"}), 422
        
    logger.info("Processing completed successfully.")
    return jsonify({"status": "processed", "result": "success"})

if __name__ == '__main__':
    # Start the "chaos monkey" crash simulator in the background
    threading.Thread(target=crash_simulator, daemon=True).start()
    
    logger.info("Starting Flask Observability application on port 5000")
    app.run(host='0.0.0.0', port=5000)
