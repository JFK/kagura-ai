# Kagura Memory Cloud - GCP Deployment Guide

Complete guide for deploying Kagura AI to Google Cloud Platform (GCP).

## 📋 Prerequisites

### 1. GCP Project Setup
- **Project ID**: `kagura-memory-cloud`
- **Region**: `asia-northeast1` (Tokyo)
- **Billing**: Enabled (~$57-62/month)

### 2. Local Requirements
- Terraform >= 1.13
- gcloud CLI configured
- SSH key pair (`~/.ssh/id_rsa.pub`)

### 3. Domain Configuration
- **Domain**: `memory.kagura-ai.com`
- **DNS**: A record → VM External IP (already configured ✅)

### 4. Google Cloud Console Setup

#### OAuth2 Client ID (for Issue #650):
1. Go to: https://console.cloud.google.com/apis/credentials
2. Create **OAuth 2.0 Client ID** (Web application)
3. Add **Authorized redirect URIs**:
   - `https://memory.kagura-ai.com/auth/callback`
   - `http://localhost:3000/auth/callback` (for local testing)
4. Copy **Client ID** and **Client Secret**

#### API Keys:
1. **OpenAI API**: https://platform.openai.com/api-keys
   - Create project key
   - Used for embeddings ($0.02/1M tokens)

---

## 🚀 Deployment Steps

### Step 1: Deploy Infrastructure with Terraform

```bash
cd terraform/gcp

# Configure variables
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars (set db_password, etc.)

# Initialize Terraform
terraform init

# Review plan
terraform plan

# Apply (creates VM, PostgreSQL, Redis, Storage Bucket)
terraform apply

# Note Terraform outputs (you'll need them):
# - vm_external_ip
# - postgres_public_ip
# - redis_host
# - database_url
# - redis_url
```

**Expected Infrastructure:**
- ✅ Compute Engine VM (`e2-medium`, 2 vCPU, 4GB RAM, Ubuntu 22.04)
- ✅ Cloud SQL PostgreSQL (`db-f1-micro`, POSTGRES_16)
- ✅ Memorystore Redis (`BASIC`, 1GB)
- ✅ Cloud Storage Bucket (backups)
- ✅ Firewall Rules (SSH, HTTP, HTTPS)
- ✅ Static IP Address

**Estimated time:** 10-15 minutes

---

### Step 2: SSH into VM

```bash
# SSH into the newly created VM
gcloud compute ssh kagura-memory-cloud --zone=asia-northeast1-a

# OR use output command:
terraform output -raw ssh_command | bash
```

---

### Step 3: Configure Application Secrets

On the VM:

```bash
# Navigate to application directory (created by startup script)
cd /opt/kagura

# Clone repository (if not done automatically)
git clone https://github.com/JFK/kagura-ai.git .

# Copy environment template
cp .env.cloud.example .env.cloud

# Edit .env.cloud with your secrets
nano .env.cloud
```

**Required Configuration in `.env.cloud`:**

```bash
# 1. Database & Redis (from Terraform outputs)
DATABASE_URL=postgresql://kagura_admin:YOUR_PASSWORD@POSTGRES_IP:5432/kagura
REDIS_URL=redis://REDIS_HOST:6379

# 2. OpenAI API Key (from https://platform.openai.com/api-keys)
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxx

# 3. Google OAuth2 (from Google Cloud Console)
GOOGLE_CLIENT_ID=123456789-abc.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxx
GOOGLE_REDIRECT_URI=https://memory.kagura-ai.com/auth/callback

# 4. Security Secrets (generate with openssl)
API_KEY_SECRET=$(openssl rand -hex 32)
JWT_SECRET=$(openssl rand -hex 32)

# 5. Domain
DOMAIN=memory.kagura-ai.com
ALLOWED_ORIGINS=https://memory.kagura-ai.com,https://claude.ai,https://chat.openai.com
CADDY_ADMIN_EMAIL=fumikazu.kiyota@gmail.com
```

**Quick Secret Generation:**
```bash
# Generate all secrets at once
cat <<EOF >> .env.cloud
API_KEY_SECRET=$(openssl rand -hex 32)
JWT_SECRET=$(openssl rand -hex 32)
EOF
```

---

### Step 4: Deploy Application with Docker Compose

```bash
# Still on VM (/opt/kagura)

# Verify Docker is installed (startup script should have done this)
docker --version
docker-compose --version

# Pull images and start services
docker-compose -f docker-compose.cloud.yml up -d

# Check status
docker-compose -f docker-compose.cloud.yml ps

# View logs
docker-compose -f docker-compose.cloud.yml logs -f api
```

**Expected Services:**
- ✅ `kagura-api` - FastAPI backend (port 8080 internal)
- ✅ `kagura-qdrant` - Vector database (port 6333 internal)
- ✅ `kagura-caddy` - HTTPS reverse proxy (ports 80, 443 external)

---

### Step 5: Verify Deployment

#### Check Health Endpoint:
```bash
curl https://memory.kagura-ai.com/api/v1/health
# Expected: {"status": "healthy", ...}
```

#### Check HTTPS Certificate:
```bash
curl -I https://memory.kagura-ai.com
# Should show: HTTP/2 200 with valid Let's Encrypt certificate
```

#### Test OAuth2 Login:
Open browser: `https://memory.kagura-ai.com/auth/login`
- Should redirect to Google OAuth2 consent screen

---

## 📊 Post-Deployment

### Monitor Services
```bash
# Service status
docker-compose -f docker-compose.cloud.yml ps

# Resource usage
docker stats

# Logs
docker-compose -f docker-compose.cloud.yml logs -f
```

### Backups

#### Database (Cloud SQL):
- ✅ Automatic daily backups (configured in Terraform)
- ✅ Point-in-time recovery enabled (7 days)
- Backup time: 03:00 JST

#### Qdrant Vector Data:
```bash
# Manual backup
docker exec kagura-qdrant tar czf /backups/qdrant-$(date +%Y%m%d).tar.gz /qdrant/storage

# Sync to Cloud Storage
gsutil cp /opt/kagura/backups/* gs://kagura-memory-cloud-kagura-backups/qdrant/
```

### Update Application:
```bash
# On VM
cd /opt/kagura
git pull
docker-compose -f docker-compose.cloud.yml pull
docker-compose -f docker-compose.cloud.yml up -d
```

---

## 🔧 Troubleshooting

### Cannot SSH into VM:
```bash
# Check VM status
gcloud compute instances list --project=kagura-memory-cloud

# Check firewall
gcloud compute firewall-rules list --project=kagura-memory-cloud | grep ssh
```

### Database Connection Issues:
```bash
# Check Cloud SQL IP
terraform output postgres_public_ip

# Test connection from VM
psql "$(terraform output -raw database_url)"
```

### HTTPS Certificate Issues:
```bash
# Check Caddy logs
docker logs kagura-caddy

# Verify DNS
nslookup memory.kagura-ai.com

# Verify firewall allows 80/443
gcloud compute firewall-rules describe kagura-allow-https
```

---

## 💰 Cost Breakdown

### Monthly Costs (asia-northeast1):
- **Compute Engine** (e2-medium): ~$24/month
- **Cloud SQL** (db-f1-micro): ~$7.50/month
- **Memorystore Redis** (1GB BASIC): ~$26/month
- **Cloud Storage** (backups): ~$0.10/month
- **Egress** (data transfer): ~$0-5/month

**Total: ~$57.50-62/month**

### API Costs (Usage-based):
- **OpenAI Embeddings**: $0.02/1M tokens (~$0.02-0.20/month typical)
- **Let's Encrypt**: Free

**Grand Total: ~$58-62/month**

---

## 🔒 Security Checklist

- [ ] SSH access restricted to your IP (update `ssh_source_ranges` in terraform.tfvars)
- [ ] Strong database password (32+ characters)
- [ ] API_KEY_SECRET and JWT_SECRET generated with `openssl rand`
- [ ] .env.cloud permissions: `chmod 600 .env.cloud`
- [ ] Google OAuth2 redirect URIs match domain
- [ ] HTTPS certificate valid (Let's Encrypt)
- [ ] Cloud SQL deletion protection enabled
- [ ] Regular backups verified

---

## 📚 Related Documentation

- **Architecture**: `../../docs/deployment/gcp.md`
- **Issue #554**: Cloud-Native Infrastructure Migration
- **Issue #650**: OAuth2 & API Key Management
- **Terraform Main**: `main.tf`
- **Environment Variables**: `../../.env.cloud.example`

---

## 🆘 Support

- **GitHub Issues**: https://github.com/JFK/kagura-ai/issues
- **Discussions**: https://github.com/JFK/kagura-ai/discussions
- **Email**: fumikazu.kiyota@gmail.com
