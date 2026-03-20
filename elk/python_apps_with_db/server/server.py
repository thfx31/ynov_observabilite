import time
import random
import logging
import threading
import sys
import os
from flask import Flask, request, jsonify
from prometheus_flask_exporter import PrometheusMetrics
from opentelemetry import trace
from opentelemetry.trace import SpanKind
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
import psycopg2
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor

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

# Dedicated TracerProvider for PostgreSQL to simulate it as a distinct Service
db_resource = Resource(attributes={"service.name": "postgresql"})
db_provider = TracerProvider(resource=db_resource)
db_provider.add_span_processor(span_processor)

# Instrument Psycopg2 for tracing using the dedicated provider
# enable_commenter adds SQL comments to better link traces to queries
Psycopg2Instrumentor().instrument(tracer_provider=db_provider, enable_commenter=True)

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

def get_db_connection():
    """
    Returns a new connection to the PostgreSQL database using environment variables.
    """
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "db"),
        database=os.getenv("DB_NAME", "postgres"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
        connect_timeout=5
    )

def init_db():
    """
    Initializes the database: waits for connection, creates table, and inserts sample data.
    """
    logger.info("Initializing database connection and schema...")
    max_retries = 10
    for i in range(max_retries):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            # Create table if it doesn't exist
            cur.execute("CREATE TABLE IF NOT EXISTS lab_data (id SERIAL PRIMARY KEY, value INTEGER);")
            
            # Insert sample data if empty
            cur.execute("SELECT COUNT(*) FROM lab_data;")
            if cur.fetchone()[0] == 0:
                logger.info("Database empty. Inserting sample data matching original API.")
                sample_values = [1, 2, 3, 4, 5]
                for val in sample_values:
                    cur.execute("INSERT INTO lab_data (value) VALUES (%s);", (val,))
                conn.commit()
                logger.info("Sample data inserted successfully.")
            
            cur.close()
            conn.close()
            logger.info("Database initialization complete.")
            return True
        except Exception as e:
            logger.warning(f"Database connection attempt {i+1}/{max_retries} failed: {e}")
            time.sleep(3)
    
    logger.critical("Failed to connect to database after multiple retries. Exiting.")
    sys.exit(1)

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
        
    # Simulate random 500 internal server errors (keeping existing logic for the lab)
    if random.random() < 0.1:
        logger.error("Failed to fetch data from the database. Simulated database connection timeout.")
        return jsonify({"error": "Database connection failed", "details": "Timeout"}), 500
        
    try:
        with tracer.start_as_current_span(
            "fetch-data-from-db", 
            kind=SpanKind.CLIENT,
            attributes={
                "db.system": "postgresql",
                "db.name": os.getenv("DB_NAME", "postgres"),
                "db.statement": "SELECT value FROM lab_data ORDER BY id;",
                "peer.service": "postgresql"
            }
        ):
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT value FROM lab_data ORDER BY id;")
            rows = cur.fetchall()
            data = [row[0] for row in rows]
            cur.close()
            conn.close()
            
        logger.info(f"Successfully fetched {len(data)} items from PostgreSQL database.")
        return jsonify({"data": data, "count": len(data)})
    except Exception as e:
        logger.error(f"Unexpected error querying PostgreSQL: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

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

@app.route('/fake')
def fake_query():
    logger.debug("Received request on /fake endpoint")
    try:
        with tracer.start_as_current_span(
            "fake-failing-db-query", 
            kind=SpanKind.CLIENT,
            attributes={
                "db.system": "postgresql",
                "db.name": os.getenv("DB_NAME", "postgres"),
                "db.statement": "SELECT * FROM non_existent_table;",
                "peer.service": "postgresql"
            }
        ):
            conn = get_db_connection()
            cur = conn.cursor()
            # This query will purposely fail to generate a PostgreSQL error log
            cur.execute("SELECT * FROM non_existent_table;")
            cur.fetchall()
            cur.close()
            conn.close()
    except Exception as e:
        logger.error(f"Intentional database error triggered on /fake: {e}")
        return jsonify({"error": "Fake query failed", "details": str(e)}), 500
        
    return jsonify({"warning": "This should not have succeeded"}), 200

if __name__ == '__main__':
    # Initialize database before starting the server

    init_db()
    
    # Start the "chaos monkey" crash simulator in the background
    threading.Thread(target=crash_simulator, daemon=True).start()
    
    logger.info("Starting Flask Observability application on port 5000")
    app.run(host='0.0.0.0', port=5000)
