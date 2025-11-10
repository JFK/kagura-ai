#!/bin/bash
# Kagura Memory Cloud - GCP Deployment Script
# https://github.com/JFK/kagura-ai/issues/649

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Kagura Memory Cloud - GCP Deployment${NC}"
echo

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not found. Please install: https://cloud.google.com/sdk/docs/install${NC}"
    exit 1
fi

# Check if terraform is installed
if ! command -v terraform &> /dev/null; then
    echo -e "${RED}❌ Terraform not found. Please install: https://www.terraform.io/downloads${NC}"
    exit 1
fi

# Get VM name from terraform output
VM_NAME=$(cd terraform/gcp && terraform output -raw vm_name 2>/dev/null || echo "kagura-memory-cloud")
VM_ZONE=$(cd terraform/gcp && terraform output -raw vm_zone 2>/dev/null || echo "asia-northeast1-a")

echo -e "${YELLOW}📋 Deployment Configuration:${NC}"
echo "  VM Name: $VM_NAME"
echo "  VM Zone: $VM_ZONE"
echo

# Setup VM for deployment
echo -e "${YELLOW}📦 Setting up VM...${NC}"

# Create remote directory with proper permissions
gcloud compute ssh $VM_NAME --zone=$VM_ZONE --command="sudo mkdir -p /opt/kagura && sudo chown -R \$USER:\$USER /opt/kagura && sudo chmod 755 /opt/kagura"

# Check if repository exists on VM
echo -e "${YELLOW}📦 Checking repository on VM...${NC}"

REPO_EXISTS=$(gcloud compute ssh $VM_NAME --zone=$VM_ZONE --command="test -d /opt/kagura/.git && echo 'yes' || echo 'no'")

if [ "$REPO_EXISTS" = "yes" ]; then
    echo -e "${GREEN}  ✓ Repository exists, pulling latest changes${NC}"
    gcloud compute ssh $VM_NAME --zone=$VM_ZONE --command="cd /opt/kagura && git fetch origin && git checkout v4.4.0-release && git pull origin v4.4.0-release"
else
    echo -e "${YELLOW}  Setting up repository on VM...${NC}"

    # Check if /opt/kagura directory exists
    DIR_EXISTS=$(gcloud compute ssh $VM_NAME --zone=$VM_ZONE --command="test -d /opt/kagura && echo 'yes' || echo 'no'")

    if [ "$DIR_EXISTS" = "yes" ]; then
        # Directory exists but not a git repo - remove and clone fresh
        echo -e "${YELLOW}  Removing existing non-git directory...${NC}"
        gcloud compute ssh $VM_NAME --zone=$VM_ZONE --command="sudo rm -rf /opt/kagura"
    fi

    echo -e "${YELLOW}  Cloning repository to VM...${NC}"
    gcloud compute ssh $VM_NAME --zone=$VM_ZONE --command="cd /tmp && git clone -b v4.4.0-release https://github.com/JFK/kagura-ai.git kagura && sudo mv /tmp/kagura /opt/kagura && sudo chown -R \$USER:\$USER /opt/kagura"
fi

# Copy configuration files
echo -e "${YELLOW}📦 Copying configuration files...${NC}"

gcloud compute scp docker-compose.cloud.yml $VM_NAME:/opt/kagura/docker-compose.yml --zone=$VM_ZONE
gcloud compute scp Caddyfile.cloud $VM_NAME:/opt/kagura/Caddyfile --zone=$VM_ZONE

# Copy .env file (if exists)
if [ -f .env ]; then
    echo -e "${GREEN}  ✓ Copying .env file${NC}"
    gcloud compute scp .env $VM_NAME:/opt/kagura/.env --zone=$VM_ZONE
else
    echo -e "${YELLOW}  ⚠ .env file not found. Please create it on the VM manually.${NC}"
fi

echo -e "${GREEN}  ✓ Files ready${NC}"
echo

# Build and start containers
echo -e "${YELLOW}🐳 Building and deploying containers...${NC}"
echo -e "${YELLOW}  This may take 5-10 minutes on first run...${NC}"

gcloud compute ssh $VM_NAME --zone=$VM_ZONE --command="
    cd /opt/kagura

    # Use sudo for docker commands (user not yet in docker group session)
    # Build API image from source (no GHCR pull needed)
    sudo docker-compose build --no-cache api

    # Pull other images (caddy, qdrant)
    sudo docker-compose pull caddy qdrant

    # Start all services
    sudo docker-compose up -d

    # Show status
    sudo docker-compose ps
"

echo
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo

# Get domain from .env file
DOMAIN=$(grep "^DOMAIN=" .env 2>/dev/null | cut -d'=' -f2)
if [ -z "$DOMAIN" ]; then
    DOMAIN="memory.kagura-ai.com"
fi

VM_IP=$(cd terraform/gcp && terraform output -raw vm_external_ip 2>/dev/null)
if [ -z "$VM_IP" ]; then
    VM_IP="YOUR_VM_IP"
fi

echo -e "${YELLOW}📝 Verification & Next Steps:${NC}"
echo
echo -e "${BLUE}1. Check container status:${NC}"
echo "   gcloud compute ssh $VM_NAME --zone=$VM_ZONE --command='sudo docker-compose -f /opt/kagura/docker-compose.yml ps'"
echo
echo -e "${BLUE}2. View logs:${NC}"
echo "   gcloud compute ssh $VM_NAME --zone=$VM_ZONE --command='sudo docker-compose -f /opt/kagura/docker-compose.yml logs -f'"
echo
echo -e "${BLUE}3. Test API (via IP - should work immediately):${NC}"
echo "   curl http://${VM_IP}/api/v1/health"
echo
echo -e "${BLUE}4. Test API (via domain - after DNS propagation):${NC}"
echo "   # Wait 5-10 minutes for DNS to propagate, then:"
echo "   dig ${DOMAIN}  # Should return ${VM_IP}"
echo "   curl https://${DOMAIN}/api/v1/health"
echo
echo -e "${BLUE}5. View API documentation:${NC}"
echo "   https://${DOMAIN}/api/v1/docs"
echo
echo -e "${YELLOW}⚠ Important Notes:${NC}"
echo "  📍 VM IP: ${VM_IP}"
echo "  🌐 Domain: ${DOMAIN}"
echo "  🔒 DNS propagation: 5-10 minutes (use 'dig ${DOMAIN}' to check)"
echo "  🔐 HTTPS certificate: Caddy auto-generates after DNS resolves (1-2 min)"
echo "  📊 First deployment: Check logs if containers don't start"
echo
echo -e "${GREEN}🎉 Kagura Memory Cloud is deploying!${NC}"
echo
