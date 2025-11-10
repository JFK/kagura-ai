#!/bin/bash
# Kagura Memory Cloud - Docker Installation Script for GCP VM
# This script runs on first boot of the Compute Engine instance

set -e

echo "🚀 Starting Kagura Memory Cloud setup..."

# Update system
echo "📦 Updating system packages..."
apt-get update
apt-get upgrade -y

# Install dependencies
echo "📦 Installing dependencies..."
apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git \
    ufw

# Install Docker
echo "🐳 Installing Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
rm get-docker.sh

# Install Docker Compose
echo "🐳 Installing Docker Compose..."
DOCKER_COMPOSE_VERSION="2.24.0"
curl -L "https://github.com/docker/compose/releases/download/v${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Start Docker
systemctl enable docker
systemctl start docker

# Add ubuntu user to docker group
usermod -aG docker ubuntu

# Configure firewall
echo "🔥 Configuring firewall..."
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# Create application directory
echo "📁 Creating application directory..."
mkdir -p /opt/kagura
chown ubuntu:ubuntu /opt/kagura

# Clone repository (optional - can be done via CI/CD)
# su - ubuntu -c "cd /opt/kagura && git clone https://github.com/JFK/kagura-ai.git ."

echo "✅ Kagura Memory Cloud setup complete!"
echo "📝 Next steps:"
echo "   1. SSH into the VM: gcloud compute ssh kagura-memory-cloud"
echo "   2. Deploy application: cd /opt/kagura && docker-compose -f docker-compose.cloud.yml up -d"
