#!/bin/bash
# LLM Gateway Deployment Script
# Usage: bash deploy.sh <SERVER_IP> [SSH_USER]

set -euo pipefail

SERVER_IP="${1:?Usage: bash deploy.sh <SERVER_IP> [SSH_USER]}"
SSH_USER="${2:-root}"
PROJECT_DIR="D:/code/llm-gateway"
REMOTE_DIR="/opt/llm-gateway"

echo "=== LLM Gateway Deployment ==="
echo "Target: ${SSH_USER}@${SERVER_IP}"
echo ""

# 1. Check local files
echo "[1/6] Checking local files..."
if [ ! -f "${PROJECT_DIR}/.env.prod" ]; then
    echo "ERROR: .env.prod not found. Create it first."
    exit 1
fi
echo "  .env.prod found"

# 2. Generate SSL cert if needed
echo "[2/6] Setting up SSL certificates..."
if [ ! -f "${PROJECT_DIR}/nginx/ssl/cert.pem" ]; then
    mkdir -p "${PROJECT_DIR}/nginx/ssl"
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "${PROJECT_DIR}/nginx/ssl/key.pem" \
        -out "${PROJECT_DIR}/nginx/ssl/cert.pem" \
        -subj "/C=CN/ST=Shanghai/L=Shanghai/O=LLM-Gateway/CN=${SERVER_IP}"
    echo "  Self-signed certificate generated"
else
    echo "  SSL cert already exists"
fi

# 3. Create remote directory
echo "[3/6] Setting up remote server..."
ssh "${SSH_USER}@${SERVER_IP}" "mkdir -p ${REMOTE_DIR}/nginx/ssl"

# 4. Copy files to server
echo "[4/6] Copying project files..."
rsync -avz --exclude '.git' --exclude '__pycache__' --exclude '*.pyc' \
    --exclude 'node_modules' --exclude 'dist' --exclude '.venv' \
    --exclude '.env.dev' --exclude '.firecrawl' \
    "${PROJECT_DIR}/" "${SSH_USER}@${SERVER_IP}:${REMOTE_DIR}/"

# 5. Copy and activate production .env
echo "[5/6] Setting up production environment..."
ssh "${SSH_USER}@${SERVER_IP}" "cp ${REMOTE_DIR}/.env.prod ${REMOTE_DIR}/.env"

# 6. Build and start
echo "[6/6] Starting services..."
ssh "${SSH_USER}@${SERVER_IP}" << 'ENDSSH'
cd /opt/llm-gateway

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com | bash
fi

# Start services
docker compose down 2>/dev/null || true
docker compose up -d --build

# Wait for services
echo "Waiting for services to be ready..."
sleep 10

# Show status
echo ""
echo "=== Service Status ==="
docker compose ps

echo ""
echo "=== Health Checks ==="
curl -sk https://localhost/health 2>/dev/null || echo "  (checking...)"
curl -sk https://localhost/admin/api/health 2>/dev/null || echo "  (checking...)"

echo ""
echo "=== Deployment Complete ==="
echo "Access at: https://${SERVER_IP}"
echo "Admin: https://${SERVER_IP}/admin"
echo "Default login: admin@example.com / Admin123"
echo ""
echo "IMPORTANT next steps:"
echo "  1. Change the admin password immediately"
echo "  2. Set a real OPENAI_API_KEY in .env and restart"
echo "  3. Configure SMTP settings for email verification"
echo "  4. Get a domain and real SSL certificate"
ENDSSH

echo ""
echo "Done!"
