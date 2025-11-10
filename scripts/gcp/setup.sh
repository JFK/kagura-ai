#!/bin/bash
# Kagura Memory Cloud - GCP Infrastructure Setup Script
# https://github.com/JFK/kagura-ai/issues/649

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Kagura Memory Cloud - GCP Infrastructure Setup${NC}"
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

# Step 1: GCP Project Setup
echo -e "${BLUE}📋 Step 1: GCP Project Setup${NC}"
echo

# Check if user is logged in
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo -e "${YELLOW}  ⚠ Not logged in to gcloud. Initiating login...${NC}"
    gcloud auth login
fi

echo -e "${YELLOW}  Current GCP configuration:${NC}"
gcloud config list

echo

# Get current project (handle unset case)
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null || echo "")

if [ -z "$CURRENT_PROJECT" ] || [ "$CURRENT_PROJECT" = "(unset)" ]; then
    echo -e "${YELLOW}  ⚠ No project currently set${NC}"
    CURRENT_PROJECT=""
else
    echo -e "${YELLOW}  Current project: ${CURRENT_PROJECT}${NC}"
fi

# Ask if user wants to select a project
if [ -n "$CURRENT_PROJECT" ]; then
    read -p "  Use current project '$CURRENT_PROJECT'? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        PROJECT_ID="$CURRENT_PROJECT"
    else
        PROJECT_ID=""
    fi
else
    PROJECT_ID=""
fi

# If no project selected, show available projects
if [ -z "$PROJECT_ID" ]; then
    echo -e "${YELLOW}  Available projects:${NC}"
    gcloud projects list --format="table(projectId,name,projectNumber)"
    echo
    read -p "  Enter project ID to use (or 'new' to create): " PROJECT_ID

    if [ "$PROJECT_ID" == "new" ]; then
        read -p "  Enter new project ID (lowercase, hyphens only): " PROJECT_ID
        read -p "  Enter project name: " PROJECT_NAME

        echo -e "${YELLOW}  Creating new project...${NC}"
        gcloud projects create $PROJECT_ID --name="$PROJECT_NAME"

        echo -e "${YELLOW}  Linking billing account...${NC}"
        echo -e "${BLUE}  Available billing accounts:${NC}"
        gcloud billing accounts list
        read -p "  Enter billing account ID: " BILLING_ACCOUNT
        gcloud billing projects link $PROJECT_ID --billing-account=$BILLING_ACCOUNT
    fi

    # Set project
    gcloud config set project $PROJECT_ID
fi

# Verify project is set
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" = "(unset)" ]; then
    echo -e "${RED}  ❌ Failed to set project. Please run manually:${NC}"
    echo -e "     gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo -e "${GREEN}  ✓ Using project: $PROJECT_ID${NC}"

# Check billing is enabled
echo -e "${YELLOW}  Checking billing status...${NC}"
BILLING_ENABLED=$(gcloud beta billing projects describe $PROJECT_ID --format="value(billingEnabled)" 2>/dev/null || echo "false")

if [ "$BILLING_ENABLED" != "True" ]; then
    echo -e "${RED}  ❌ Billing not enabled for project $PROJECT_ID${NC}"
    echo -e "${YELLOW}  Available billing accounts:${NC}"
    gcloud billing accounts list
    echo
    read -p "  Enter billing account ID to link: " BILLING_ACCOUNT
    gcloud billing projects link $PROJECT_ID --billing-account=$BILLING_ACCOUNT
    echo -e "${GREEN}  ✓ Billing enabled${NC}"
else
    echo -e "${GREEN}  ✓ Billing already enabled${NC}"
fi

# Step 2: Enable Required APIs
echo
echo -e "${BLUE}📋 Step 2: Enabling Required APIs${NC}"
echo -e "${YELLOW}  This may take a few minutes...${NC}"

APIS=(
    "compute.googleapis.com"
    "sqladmin.googleapis.com"
    "redis.googleapis.com"
    "storage-api.googleapis.com"
    "iam.googleapis.com"
)

for api in "${APIS[@]}"; do
    echo -e "${YELLOW}  Enabling $api...${NC}"
    gcloud services enable $api
done

echo -e "${GREEN}  ✓ All APIs enabled${NC}"

# Step 3: Application Default Credentials for Terraform
echo
echo -e "${BLUE}📋 Step 3: Setup Application Default Credentials${NC}"
echo -e "${YELLOW}  Terraform requires application default credentials...${NC}"

# Check if ADC is already set up
if [ ! -f "$HOME/.config/gcloud/application_default_credentials.json" ]; then
    echo -e "${YELLOW}  Running 'gcloud auth application-default login'...${NC}"
    gcloud auth application-default login
    echo -e "${GREEN}  ✓ Application default credentials configured${NC}"
else
    echo -e "${GREEN}  ✓ Application default credentials already configured${NC}"
fi

# Step 4: Terraform Configuration
echo
echo -e "${BLUE}📋 Step 4: Terraform Configuration${NC}"

cd terraform/gcp

if [ ! -f terraform.tfvars ]; then
    echo -e "${YELLOW}  Creating terraform.tfvars from example...${NC}"
    cp terraform.tfvars.example terraform.tfvars

    # Update project_id automatically
    sed -i "s/your-gcp-project-id/$PROJECT_ID/g" terraform.tfvars

    echo -e "${GREEN}  ✓ terraform.tfvars created${NC}"
    echo -e "${RED}  ⚠ IMPORTANT: Edit terraform.tfvars and set:${NC}"
    echo "    - db_password (use a strong password!)"
    echo "    - ssh_source_ranges (restrict to your IP)"
    echo
    read -p "  Press Enter to edit terraform.tfvars..." -r
    ${EDITOR:-nano} terraform.tfvars
else
    echo -e "${YELLOW}  terraform.tfvars already exists${NC}"
fi

# Step 5: Terraform Init & Plan
echo
echo -e "${BLUE}📋 Step 5: Terraform Infrastructure Deployment${NC}"

echo -e "${YELLOW}  Initializing Terraform...${NC}"
terraform init

echo
echo -e "${YELLOW}  Planning infrastructure changes...${NC}"
terraform plan -out=tfplan

echo
echo -e "${YELLOW}  Estimated monthly cost:${NC}"
echo "    - Compute Engine (e2-medium): ~\$24/month"
echo "    - Cloud SQL (db-f1-micro): ~\$7.50/month"
echo "    - Memorystore Redis (1GB): ~\$26/month"
echo "    - Total: ~\$57.50-62/month"
echo
read -p "  Do you want to apply this plan? (yes/no): " -r
echo

if [[ $REPLY == "yes" ]]; then
    echo -e "${YELLOW}  Applying Terraform plan...${NC}"
    terraform apply tfplan

    echo -e "${GREEN}  ✓ Infrastructure deployed!${NC}"

    # Save outputs
    echo
    echo -e "${BLUE}📋 Infrastructure Outputs:${NC}"
    terraform output

    # Export connection strings
    echo
    echo -e "${YELLOW}  Saving connection strings to ../../.env${NC}"
    cd ../..

    if [ ! -f .env ]; then
        cp .env.cloud.example .env
    fi

    # Update .env with terraform outputs
    DATABASE_URL=$(cd terraform/gcp && terraform output -raw database_url)
    REDIS_URL=$(cd terraform/gcp && terraform output -raw redis_url)
    VM_IP=$(cd terraform/gcp && terraform output -raw vm_external_ip)

    sed -i "s|DATABASE_URL=.*|DATABASE_URL=$DATABASE_URL|g" .env
    sed -i "s|REDIS_URL=.*|REDIS_URL=$REDIS_URL|g" .env

    echo -e "${GREEN}  ✓ .env updated with connection strings${NC}"
    echo -e "${RED}  ⚠ IMPORTANT: Edit .env and set remaining values:${NC}"
    echo "    - API_KEY_SECRET"
    echo "    - JWT_SECRET"
    echo "    - GOOGLE_CLIENT_ID"
    echo "    - GOOGLE_CLIENT_SECRET"
    echo "    - DOMAIN"

    echo
    echo -e "${GREEN}✅ GCP Infrastructure Setup Complete!${NC}"
    echo
    echo -e "${YELLOW}📝 Next Steps:${NC}"
    echo "  1. Configure DNS: Point your domain to $VM_IP"
    echo "  2. Edit .env file and set all required values"
    echo "  3. Deploy application: ./scripts/gcp/deploy.sh"
    echo
else
    echo -e "${YELLOW}  Skipping infrastructure deployment${NC}"
    rm tfplan
fi
