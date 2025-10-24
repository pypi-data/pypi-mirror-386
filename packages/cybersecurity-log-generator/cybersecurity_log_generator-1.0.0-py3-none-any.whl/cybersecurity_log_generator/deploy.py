#!/usr/bin/env python3
"""
Production Deployment Script for Cybersecurity Log Generator MCP Server
Supports multiple deployment strategies and configurations
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

def create_dockerfile():
    """Create Dockerfile for containerized deployment."""
    dockerfile_content = """# Cybersecurity Log Generator MCP Server Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 mcpuser && chown -R mcpuser:mcpuser /app
USER mcpuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/mcp/health || exit 1

# Run the server
CMD ["python", "remote_mcp_server.py", "--production", "--host", "0.0.0.0", "--port", "8000"]
"""
    
    with open("Dockerfile", "w") as f:
        f.write(dockerfile_content)
    print("✅ Created Dockerfile")

def create_requirements():
    """Create requirements.txt for deployment."""
    requirements = """# Cybersecurity Log Generator MCP Server Requirements
fastmcp>=2.0.0
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
starlette>=0.27.0
pydantic>=2.0.0
faker>=19.0.0
requests>=2.31.0
python-multipart>=0.0.6
"""
    
    with open("requirements.txt", "w") as f:
        f.write(requirements)
    print("✅ Created requirements.txt")

def create_docker_compose():
    """Create docker-compose.yml for easy deployment."""
    compose_content = """version: '3.8'

services:
  mcp-server:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MCP_AUTH_TOKEN=${MCP_AUTH_TOKEN:-}
      - PYTHONPATH=/app
    volumes:
      - ./logs:/app/logs
      - ./exports:/app/exports
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/mcp/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Optional: Add Redis for session storage
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
"""
    
    with open("docker-compose.yml", "w") as f:
        f.write(compose_content)
    print("✅ Created docker-compose.yml")

def create_environment_template():
    """Create environment template for configuration."""
    env_template = """# Cybersecurity Log Generator MCP Server Environment Configuration

# Authentication (optional but recommended for production)
MCP_AUTH_TOKEN=your-secret-token-here

# Server Configuration
HOST=0.0.0.0
PORT=8000
WORKERS=4

# Logging
LOG_LEVEL=info
LOG_FORMAT=json

# Export Configuration
EXPORT_BASE_PATH=/app/exports
LOG_RETENTION_DAYS=30

# Optional: Redis Configuration
REDIS_URL=redis://redis:6379/0

# Optional: VictoriaLogs Integration
VICTORIALOGS_URL=http://victorialogs:9428
VICTORIALOGS_INGEST=false
"""
    
    with open(".env.template", "w") as f:
        f.write(env_template)
    print("✅ Created .env.template")

def create_kubernetes_manifests():
    """Create Kubernetes deployment manifests."""
    
    # Deployment
    deployment = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-server
  labels:
    app: mcp-server
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mcp-server
  template:
    metadata:
      labels:
        app: mcp-server
    spec:
      containers:
      - name: mcp-server
        image: cybersecurity-log-generator:latest
        ports:
        - containerPort: 8000
        env:
        - name: MCP_AUTH_TOKEN
          valueFrom:
            secretKeyRef:
              name: mcp-secrets
              key: auth-token
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /mcp/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /mcp/health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
"""
    
    # Service
    service = """apiVersion: v1
kind: Service
metadata:
  name: mcp-server-service
spec:
  selector:
    app: mcp-server
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
"""
    
    # Secret
    secret = """apiVersion: v1
kind: Secret
metadata:
  name: mcp-secrets
type: Opaque
data:
  auth-token: <base64-encoded-token>
"""
    
    os.makedirs("k8s", exist_ok=True)
    
    with open("k8s/deployment.yaml", "w") as f:
        f.write(deployment)
    with open("k8s/service.yaml", "w") as f:
        f.write(service)
    with open("k8s/secret.yaml", "w") as f:
        f.write(secret)
    
    print("✅ Created Kubernetes manifests in k8s/")

def create_nginx_config():
    """Create Nginx configuration for reverse proxy."""
    nginx_config = """server {
    listen 80;
    server_name your-domain.com;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;
    
    location /mcp/ {
        proxy_pass http://localhost:8000/mcp/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    location /health {
        proxy_pass http://localhost:8000/mcp/health;
        access_log off;
    }
}
"""
    
    with open("nginx.conf", "w") as f:
        f.write(nginx_config)
    print("✅ Created nginx.conf")

def create_startup_script():
    """Create startup script for easy deployment."""
    startup_script = """#!/bin/bash
# Cybersecurity Log Generator MCP Server Startup Script

set -e

echo "🚀 Starting Cybersecurity Log Generator MCP Server"

# Check if running in container
if [ -f /.dockerenv ]; then
    echo "📦 Running in container mode"
    export HOST=0.0.0.0
else
    echo "🖥️  Running in host mode"
    export HOST=${HOST:-127.0.0.1}
fi

# Set default values
export PORT=${PORT:-8000}
export WORKERS=${WORKERS:-1}
export LOG_LEVEL=${LOG_LEVEL:-info}

# Create necessary directories
mkdir -p logs exports

# Start the server
echo "🌐 Server will be available at: http://$HOST:$PORT/mcp/"
echo "🔧 Health check: http://$HOST:$PORT/mcp/health"
echo "📊 Status: http://$HOST:$PORT/mcp/status"

if [ "$PRODUCTION" = "true" ]; then
    echo "🏭 Starting in production mode"
    python remote_mcp_server.py --production --host $HOST --port $PORT --workers $WORKERS
else
    echo "🔧 Starting in development mode"
    python remote_mcp_server.py --host $HOST --port $PORT --reload
fi
"""
    
    with open("start.sh", "w") as f:
        f.write(startup_script)
    
    # Make executable
    os.chmod("start.sh", 0o755)
    print("✅ Created start.sh")

def create_monitoring_config():
    """Create monitoring configuration."""
    prometheus_config = """# Prometheus configuration for MCP Server monitoring
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'mcp-server'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/mcp/metrics'
    scrape_interval: 30s
"""
    
    with open("prometheus.yml", "w") as f:
        f.write(prometheus_config)
    print("✅ Created prometheus.yml")

def main():
    parser = argparse.ArgumentParser(description="Create deployment configuration")
    parser.add_argument("--type", choices=["docker", "k8s", "nginx", "all"], 
                       default="all", help="Type of deployment configuration to create")
    parser.add_argument("--output-dir", default=".", help="Output directory for files")
    
    args = parser.parse_args()
    
    # Change to output directory
    os.chdir(args.output_dir)
    
    print("🔧 Creating deployment configuration for Cybersecurity Log Generator MCP Server")
    print("=" * 70)
    
    if args.type in ["docker", "all"]:
        create_dockerfile()
        create_requirements()
        create_docker_compose()
        create_environment_template()
        create_startup_script()
    
    if args.type in ["k8s", "all"]:
        create_kubernetes_manifests()
    
    if args.type in ["nginx", "all"]:
        create_nginx_config()
    
    if args.type == "all":
        create_monitoring_config()
    
    print("\n🎉 Deployment configuration created successfully!")
    print("\n📋 Next steps:")
    print("1. Configure environment variables in .env.template")
    print("2. Choose your deployment method:")
    print("   - Docker: docker-compose up -d")
    print("   - Kubernetes: kubectl apply -f k8s/")
    print("   - Direct: python remote_mcp_server.py --production")
    print("\n🔗 Server will be available at: http://localhost:8000/mcp/")

if __name__ == "__main__":
    main()
