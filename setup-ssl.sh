#!/bin/bash
# SSL Certificate Setup
# Usage: bash setup-ssl.sh <DOMAIN_OR_IP>

set -euo pipefail

DOMAIN="${1:?Usage: bash setup-ssl.sh <DOMAIN_OR_IP>}"
SSL_DIR="D:/code/llm-gateway/nginx/ssl"

mkdir -p "${SSL_DIR}"

# Check if certbot is available (Let's Encrypt)
if command -v certbot &> /dev/null; then
    echo "Using Let's Encrypt (certbot)..."
    sudo certbot certonly --standalone -d "${DOMAIN}" \
        --agree-tos --non-interactive \
        --email admin@example.com
    sudo cp "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" "${SSL_DIR}/cert.pem"
    sudo cp "/etc/letsencrypt/live/${DOMAIN}/privkey.pem" "${SSL_DIR}/key.pem"
    echo "Let's Encrypt certificate installed"
else
    echo "certbot not found, generating self-signed certificate..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "${SSL_DIR}/key.pem" \
        -out "${SSL_DIR}/cert.pem" \
        -subj "/C=CN/ST=Shanghai/L=Shanghai/O=LLM-Gateway/CN=${DOMAIN}"
    echo "Self-signed certificate generated (browser will show warning)"
    echo "Install certbot and re-run for trusted certificate:"
    echo "  sudo apt install certbot && bash setup-ssl.sh ${DOMAIN}"
fi

echo "Certificate files:"
ls -la "${SSL_DIR}/"
