# Kagura Memory Cloud - GCP Deployment Guide

Complete guide for deploying Kagura Memory Cloud on Google Cloud Platform.

**Related**: [Issue #649](https://github.com/JFK/kagura-ai/issues/649)

---

## 📋 Prerequisites

### Required Tools
- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) (gcloud CLI)
- [Terraform](https://www.terraform.io/downloads) >= 1.5
- [Docker](https://docs.docker.com/get-docker/) (optional, for local testing)
- SSH key pair (`~/.ssh/id_rsa.pub`)

### GCP Account
- Active GCP account
- Billing account enabled
- Project with billing linked

### Domain (Required for HTTPS)
- Registered domain name
- Access to DNS management

---

## 🚀 Quick Start (Automated Setup)

### Option 1: All-in-One Setup Script

```bash
# Clone repository
git clone https://github.com/JFK/kagura-ai.git
cd kagura-ai

# Run automated setup
./scripts/gcp/setup.sh
```

This script will:
1. ✅ Configure GCP project
2. ✅ Enable required APIs
3. ✅ Deploy infrastructure via Terraform
4. ✅ Generate `.env` file with connection strings

After setup completes:
```bash
# 1. Configure DNS (point your domain to VM IP)
# 2. Edit .env file (set secrets, domain, OAuth2 credentials)
# 3. Deploy application
./scripts/gcp/deploy.sh
```

---

## 📚 Manual Setup (Step-by-Step)

### Step 1: GCP Project Setup

#### 1.1 Create GCP Project

```bash
# Login to gcloud
gcloud auth login

# Create project
gcloud projects create kagura-memory-cloud --name="Kagura Memory Cloud"

# Set default project
gcloud config set project kagura-memory-cloud

# Link billing account
gcloud billing accounts list
gcloud billing projects link kagura-memory-cloud --billing-account=BILLING_ACCOUNT_ID
```

#### 1.2 Enable Required APIs

```bash
# Enable APIs
gcloud services enable compute.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable redis.googleapis.com
gcloud services enable storage-api.googleapis.com
gcloud services enable iam.googleapis.com
```

---

### Step 2: Terraform Configuration

#### 2.1 Configure Variables

```bash
cd terraform/gcp

# Copy example
cp terraform.tfvars.example terraform.tfvars

# Edit configuration
nano terraform.tfvars
```

**Required variables**:
```hcl
project_id  = "kagura-memory-cloud"
region      = "asia-northeast1"  # Tokyo
zone        = "asia-northeast1-a"
environment = "production"

# Database password (IMPORTANT: Use strong password!)
db_password = "YOUR_STRONG_PASSWORD_HERE"

# SSH (IMPORTANT: Restrict to your IP!)
ssh_source_ranges = ["YOUR_IP/32"]
```

#### 2.2 Deploy Infrastructure

```bash
# Initialize Terraform
terraform init

# Preview changes
terraform plan

# Apply (deploys infrastructure)
terraform apply

# Save outputs
terraform output > outputs.txt
```

**Resources created**:
- ✅ Compute Engine VM (e2-medium, 4GB RAM)
- ✅ Cloud SQL PostgreSQL (db-f1-micro)
- ✅ Memorystore Redis (1GB)
- ✅ Cloud Storage bucket (backups)
- ✅ Static IP address
- ✅ Firewall rules

**Estimated cost**: ~$60/month

---

### Step 3: DNS Configuration

#### 3.1 Get Static IP

```bash
terraform output vm_external_ip
# Example: 35.200.123.456
```

#### 3.2 Configure DNS Records

Add the following DNS records at your domain registrar:

```
Type  Name   Value
A     @      35.200.123.456
A     www    35.200.123.456
```

**Wait 5-10 minutes** for DNS propagation.

Verify:
```bash
dig memory.yourdomain.com
```

---

### Step 4: Google OAuth2 Setup

#### 4.1 Create OAuth2 Credentials

1. Go to [Google Cloud Console - Credentials](https://console.cloud.google.com/apis/credentials)
2. Create credentials → OAuth client ID
3. Application type: Web application
4. Authorized redirect URIs:
   - `https://memory.yourdomain.com/api/v1/auth/google/callback`
   - `http://localhost:8000/api/v1/auth/google/callback` (development)
5. Save **Client ID** and **Client Secret**

---

### Step 5: Environment Configuration

#### 5.1 Create .env File

```bash
# Return to project root
cd ../..

# Copy example
cp .env.cloud.example .env

# Edit configuration
nano .env
```

#### 5.2 Set Required Values

```bash
# Database (from Terraform output)
DATABASE_URL=postgresql://kagura_admin:PASSWORD@IP:5432/kagura

# Redis (from Terraform output)
REDIS_URL=redis://IP:6379

# Domain
DOMAIN=memory.yourdomain.com
ALLOWED_ORIGINS=https://memory.yourdomain.com
CADDY_ADMIN_EMAIL=admin@yourdomain.com

# Security (generate with: openssl rand -hex 32)
API_KEY_SECRET=<random-hex-32-bytes>
JWT_SECRET=<random-hex-32-bytes>

# Google OAuth2 (from Step 4)
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxx
GOOGLE_REDIRECT_URI=https://memory.yourdomain.com/api/v1/auth/google/callback
```

**Generate secrets**:
```bash
echo "API_KEY_SECRET=$(openssl rand -hex 32)"
echo "JWT_SECRET=$(openssl rand -hex 32)"
```

---

### Step 6: Deploy Application

#### 6.1 Deploy via Script

```bash
./scripts/gcp/deploy.sh
```

This will:
1. ✅ Copy files to VM
2. ✅ Pull Docker images
3. ✅ Start containers

#### 6.2 Manual Deployment (Alternative)

```bash
# Get VM info
VM_NAME=$(cd terraform/gcp && terraform output -raw vm_name)
VM_ZONE=$(cd terraform/gcp && terraform output -raw vm_zone)

# Copy files
gcloud compute scp docker-compose.cloud.yml $VM_NAME:/opt/kagura/docker-compose.yml --zone=$VM_ZONE
gcloud compute scp Caddyfile.cloud $VM_NAME:/opt/kagura/Caddyfile --zone=$VM_ZONE
gcloud compute scp .env $VM_NAME:/opt/kagura/.env --zone=$VM_ZONE

# SSH into VM
gcloud compute ssh $VM_NAME --zone=$VM_ZONE

# On VM: Deploy
cd /opt/kagura
docker-compose pull
docker-compose up -d
```

---

### Step 7: Verify Deployment

#### 7.1 Check Services

```bash
# SSH into VM
gcloud compute ssh $VM_NAME --zone=$VM_ZONE

# Check containers
docker-compose ps

# Check logs
docker-compose logs -f
```

#### 7.2 Test API

```bash
# Health check
curl https://memory.yourdomain.com/api/v1/health

# Expected response:
# {"status": "ok", "version": "4.3.0"}

# API documentation
open https://memory.yourdomain.com/api/v1/docs
```

#### 7.3 Test OAuth2 Login

1. Go to `https://memory.yourdomain.com/auth/login`
2. Login with Google
3. Should redirect to dashboard

---

## 🔧 Operations

### Viewing Logs

```bash
# SSH into VM
gcloud compute ssh kagura-memory-cloud --zone=asia-northeast1-a

# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f api
docker-compose logs -f caddy
```

### Restarting Services

```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart api
```

### Updating Application

```bash
# On your local machine
./scripts/gcp/deploy.sh

# Or manually on VM
cd /opt/kagura
docker-compose pull
docker-compose up -d
```

### Database Backups

#### Manual Backup

```bash
# SSH into VM
gcloud compute ssh kagura-memory-cloud --zone=asia-northeast1-a

# Backup to Cloud Storage
BACKUP_FILE="backup-$(date +%Y%m%d-%H%M%S).sql.gz"
pg_dump $DATABASE_URL | gzip > $BACKUP_FILE
gsutil cp $BACKUP_FILE gs://YOUR_PROJECT-kagura-backups/
```

#### Automated Backups

Cloud SQL has automated daily backups enabled by default (retention: 7 days).

View backups:
```bash
gcloud sql backups list --instance=kagura-postgres-production
```

---

## 💰 Cost Optimization

### Current Monthly Cost: ~$60

| Service | Tier | Cost/Month |
|---------|------|------------|
| Compute Engine | e2-medium | ~$24 |
| Cloud SQL | db-f1-micro | ~$7.50 |
| Memorystore Redis | 1GB Basic | ~$26 |
| Storage | 10GB | ~$0.25 |
| **Total** | | **~$57.75** |

### Optimization Tips

#### 1. Use Committed Use Discounts (Save 57%)
```bash
# Reserve 1-year commitment for VM
# Cost: $24/month → $10/month
gcloud compute commitments create kagura-vm-1year \
  --resources=memory=4,vcpu=2 \
  --plan=12-month \
  --region=asia-northeast1
```

#### 2. Use Preemptible VMs for Dev/Staging (Save 80%)
```hcl
# In terraform/gcp/main.tf for dev environment
scheduling {
  preemptible       = true
  automatic_restart = false
}
# Cost: $24/month → $5/month
```

#### 3. Use Cloud SQL Always-Free Tier
```hcl
# Change db_tier to: db-f1-micro (up to 10GB storage)
# First instance is free!
db_tier = "db-f1-micro"
```

#### 4. Optimize Redis (Save $13/month)
```hcl
# Use 512MB Redis instead of 1GB
redis_memory_gb = 0.5
# Cost: $26/month → $13/month
```

**Optimized Monthly Cost**: ~$25-30/month

---

## 🔐 Security Best Practices

### 1. Restrict SSH Access

```hcl
# In terraform.tfvars
ssh_source_ranges = ["YOUR_IP/32"]  # Not 0.0.0.0/0!
```

### 2. Enable Cloud Armor (Optional)

```bash
# DDoS protection for production
gcloud compute security-policies create kagura-armor \
  --description="Kagura DDoS protection"
```

### 3. Rotate Secrets Regularly

```bash
# Generate new secrets every 90 days
openssl rand -hex 32
```

### 4. Monitor Security

```bash
# Enable Security Command Center
gcloud services enable securitycenter.googleapis.com

# View security findings
gcloud scc findings list organizations/YOUR_ORG_ID
```

---

## 🐛 Troubleshooting

### Issue: VM Cannot Connect to Cloud SQL

**Solution**: Check firewall rules

```bash
# Allow VM IP in Cloud SQL
gcloud sql instances patch kagura-postgres-production \
  --authorized-networks=VM_IP
```

### Issue: Let's Encrypt Certificate Error

**Solution**: Verify DNS and wait

```bash
# Check DNS propagation
dig memory.yourdomain.com

# Wait 5-10 minutes, then restart Caddy
docker-compose restart caddy
```

### Issue: Out of Memory

**Solution**: Upgrade VM tier

```hcl
# In terraform.tfvars
machine_type = "e2-standard-2"  # 8GB RAM
```

Then re-apply:
```bash
cd terraform/gcp
terraform apply
```

---

## 📚 Additional Resources

- [GCP Documentation](https://cloud.google.com/docs)
- [Terraform GCP Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [Caddy Documentation](https://caddyserver.com/docs/)
- [Kagura API Reference](../api-reference.md)
- [Issue #649 - Cloud Deployment](https://github.com/JFK/kagura-ai/issues/649)

---

## 🆘 Support

If you encounter issues:

1. Check logs: `docker-compose logs -f`
2. Review [Troubleshooting](#-troubleshooting) section
3. Open issue: https://github.com/JFK/kagura-ai/issues

---

**Last Updated**: 2025-11-10
**Maintained By**: @JFK
