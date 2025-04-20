FROM python:3.9-slim

# Install Node.js and npm
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    build-essential \
    && curl -sL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy backend requirements and install
COPY api/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install additional required packages if they're not already in requirements.txt
RUN pip install fastapi uvicorn python-multipart

# Copy all backend files
COPY api/ ./api/

# Set up the frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install

# Copy frontend source
COPY frontend/ ./
# Build the frontend
RUN npm run build

# Create a directory in the API folder to serve static files
WORKDIR /app
RUN mkdir -p api/static
RUN cp -r frontend/dist/* api/static/

# Create a script to start both backend and frontend
RUN echo '#!/bin/bash\npython -m uvicorn api.main:app --host 0.0.0.0 --port 7860' > start.sh
RUN chmod +x start.sh

# Volume for persistent data
VOLUME ["/app/api/chroma_db"]
VOLUME ["/app/api/data"]

# Expose the port that HF Spaces expects
EXPOSE 7860

# Command to run the server
CMD ["./start.sh"]
