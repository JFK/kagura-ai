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

# Copy files to VM
echo -e "${YELLOW}📦 Copying deployment files to VM...${NC}"

# Create remote directory with proper permissions
gcloud compute ssh $VM_NAME --zone=$VM_ZONE --command="sudo mkdir -p /opt/kagura && sudo chown -R \$USER:\$USER /opt/kagura && sudo chmod 755 /opt/kagura"

# Copy docker-compose and Caddyfile
gcloud compute scp docker-compose.cloud.yml $VM_NAME:/opt/kagura/docker-compose.yml --zone=$VM_ZONE
gcloud compute scp Caddyfile.cloud $VM_NAME:/opt/kagura/Caddyfile --zone=$VM_ZONE

# Copy .env file (if exists)
if [ -f .env ]; then
    echo -e "${GREEN}  ✓ Copying .env file${NC}"
    gcloud compute scp .env $VM_NAME:/opt/kagura/.env --zone=$VM_ZONE
else
    echo -e "${YELLOW}  ⚠ .env file not found. Please create it on the VM manually.${NC}"
fi

echo -e "${GREEN}  ✓ Files copied${NC}"
echo

# Pull latest images and restart services
echo -e "${YELLOW}🐳 Deploying containers...${NC}"

gcloud compute ssh $VM_NAME --zone=$VM_ZONE --command="
    cd /opt/kagura
    docker-compose pull
    docker-compose up -d
    docker-compose ps
"

echo
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo
echo -e "${YELLOW}📝 Next steps:${NC}"
echo "  1. Check logs: gcloud compute ssh $VM_NAME --zone=$VM_ZONE --command='docker-compose -C /opt/kagura logs -f'"
echo "  2. Access API: https://$(cd terraform/gcp && terraform output -raw vm_external_ip 2>/dev/null || echo 'YOUR_DOMAIN')/api/v1/health"
echo "  3. View API docs: https://YOUR_DOMAIN/api/v1/docs"
echo
