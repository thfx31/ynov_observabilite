# Observability Lab - Project

Welcome to the Project for your IT Observability course!

In this repository, you will find a mock Python/Flask application environment designed to test your observability and monitoring skills. 

## Your Mission
Your goal is to build an entire monitoring infrastructure for this application. You must implement a full observability stack (e.g., Prometheus, Grafana, Zabbix, ELK stack) to collect metrics and log data efficiently. 

**Be warned:** The API server contains a "Chaos Simulator" and is inherently unstable. It will experience critical incidents at random intervals (such as high CPU usage, memory leaks, or sudden crashes). Your monitoring stack must allow you to detect these issues as quickly as possible and diagnose the root cause using the logs and metrics.

## Server Features for the Course
1. **Metrics**: The server runs [`prometheus-flask-exporter`](https://github.com/rycus86/prometheus_flask_exporter/tree/0.23.2) which automatically binds a `/metrics` route on port 5000. Students can scrape this using Prometheus to visualize HTTP response times, request rates, 4xx/5xx error frequencies, etc.
2. **Logs**: The server creates highly detailed logs (`server.log`) using different log levels (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`). 
3. **Random Incidents**: In the background, a thread runs a "chaos simulator" that will eventually bring down the server, requiring students to monitor logs and metrics to find out exactly why the app stopped responding (e.g. CPU spike at 100%, Memory Error, or explicit crash).

## Client Features
- Simulates realistic web traffic. 
- Varies request rate randomly to create interesting traffic spikes in Prometheus.
- Creates `client.log` which tracks latency and HTTP status codes, simulating the end-user's perspective.

## Project Structure
- `server/server.py`: A Python API built with Flask. The application automatically exposes a `/metrics` endpoint for Prometheus and writes detailed, multi-level logs to `server.log`.
- `client/client.py`: A simulated user client. It continuously consumes the API, varying request rates and generating realistic traffic patterns. It also logs errors and latency from the user's perspective into `client.log`.
- `requirements.txt`: The Python dependencies required to run this application.

## Setup Instructions

### Option 1: Run with Docker (Recommended)
This is the fastest way to get the environment running with correct networking.

1. Ensure you have **Docker** and **Docker Compose** installed.
2. Run the following command from the root directory:
   ```bash
   docker compose up --build
   ```
   > **Note:** The API will be available on `http://localhost:5000` and metrics on `http://localhost:5000/metrics`.

---

### Option 2: Run Locally
If you prefer running the Python scripts directly on your host machine.

1. Install the required dependencies for both components:
   ```bash
   pip install -r server/requirements.txt
   pip install -r client/requirements.txt
   ```
2. In your first terminal, start the **API Server**:
   ```bash
   cd server
   python server.py
   ```
   > **Note:** The API will be available on `http://localhost:5000` and metrics will be exposed on `http://localhost:5000/metrics`.

3. In a second terminal, start the **Client**:
   ```bash
   cd client
   python client.py
   ```

---

## Final Steps
Once the services are running:
1. Connect your observability stack (ElasticSearch / Logstash / Kibana / etc.).
2. Monitor the metrics and logs (`server.log` and `client.log`).
3. Prepare yourself for the inevitable incident. Good luck!
