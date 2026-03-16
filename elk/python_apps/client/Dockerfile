FROM python:3.9-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the client code
COPY client.py .

# The client needs to know where the server is. 
# We'll use an environment variable that defaults to localhost but can be overridden 
# by docker-compose (e.g., http://server:5000)
ENV SERVER_URL=http://localhost:5000

# Run the client
CMD ["python", "client.py"]
