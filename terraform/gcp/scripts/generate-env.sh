#!/bin/bash
# Kagura Memory Cloud - Generate .env.cloud from Terraform outputs
#
# Usage:
#   cd terraform/gcp
#   ./scripts/generate-env.sh
#
# This script generates a partial .env.cloud file with database/redis URLs
# from Terraform outputs. You still need to add:
#   - OPENAI_API_KEY
#   - GOOGLE_CLIENT_ID
#   - GOOGLE_CLIENT_SECRET
#   - API_KEY_SECRET (generate with: openssl rand -hex 32)
#   - JWT_SECRET (generate with: openssl rand -hex 32)
#   - DOMAIN (your actual domain)

set -e

cd "$(dirname "$0")/.."

echo "🔄 Generating .env.cloud from Terraform outputs..."
echo ""

# Check if terraform state exists
if [ ! -f terraform.tfstate ]; then
    echo "❌ terraform.tfstate not found"
    echo "   Run 'terraform apply' first!"
    exit 1
fi

# Get Terraform outputs
DATABASE_URL=$(terraform output -raw database_url 2>/dev/null || echo "")
REDIS_URL=$(terraform output -raw redis_url 2>/dev/null || echo "")
POSTGRES_IP=$(terraform output -raw postgres_public_ip 2>/dev/null || echo "")
REDIS_HOST=$(terraform output -raw redis_host 2>/dev/null || echo "")
VM_IP=$(terraform output -raw vm_external_ip 2>/dev/null || echo "")

if [ -z "$DATABASE_URL" ] || [ -z "$REDIS_URL" ]; then
    echo "❌ Could not retrieve Terraform outputs"
    echo "   Ensure 'terraform apply' completed successfully"
    exit 1
fi

# Generate .env.cloud
cat <<EOF > .env.cloud.generated
# =============================================================================
# Auto-generated from Terraform outputs
# Generated: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
# =============================================================================
#
# IMPORTANT: This file contains DATABASE_URL and REDIS_URL only.
# Copy remaining secrets from .env.cloud.example and add:
#   - OPENAI_API_KEY
#   - GOOGLE_CLIENT_ID & GOOGLE_CLIENT_SECRET
#   - API_KEY_SECRET & JWT_SECRET (generate with: openssl rand -hex 32)
#   - DOMAIN (your actual domain, e.g., memory.kagura-ai.com)
#
# =============================================================================

# -----------------------------------------------------------------------------
# Infrastructure URLs (from Terraform)
# -----------------------------------------------------------------------------
DATABASE_URL=${DATABASE_URL}
REDIS_URL=${REDIS_URL}
QDRANT_URL=http://qdrant:6333

# VM External IP: ${VM_IP}
# PostgreSQL IP: ${POSTGRES_IP}
# Redis Host: ${REDIS_HOST}

# -----------------------------------------------------------------------------
# TODO: Add these manually (copy from .env.cloud.example)
# -----------------------------------------------------------------------------
# OPENAI_API_KEY=sk-proj-...
# GOOGLE_CLIENT_ID=...
# GOOGLE_CLIENT_SECRET=...
# API_KEY_SECRET=\$(openssl rand -hex 32)
# JWT_SECRET=\$(openssl rand -hex 32)
# DOMAIN=memory.yourdomain.com  # Change to your actual domain
# ALLOWED_ORIGINS=https://memory.yourdomain.com,https://claude.ai,https://chat.openai.com
# CADDY_ADMIN_EMAIL=admin@yourdomain.com
# ENVIRONMENT=production
# LOG_LEVEL=info
# EMBEDDING_PROVIDER=openai
# EMBEDDING_MODEL=text-embedding-3-small
# GRAPH_BACKEND=postgres
# PERSISTENT_BACKEND=postgres
# CACHE_BACKEND=redis
# VECTOR_BACKEND=qdrant
EOF

echo "✅ Generated: .env.cloud.generated"
echo ""
echo "📝 Next steps:"
echo "   1. Review: cat .env.cloud.generated"
echo "   2. Copy template: cp ../../.env.cloud.example .env.cloud"
echo "   3. Merge infra URLs: cat .env.cloud.generated >> .env.cloud"
echo "   4. Edit .env.cloud to add all missing secrets"
echo "   5. Secure file: chmod 600 .env.cloud"
echo ""
echo "💡 Quick secret generation:"
echo "   echo \"API_KEY_SECRET=\$(openssl rand -hex 32)\" >> .env.cloud"
echo "   echo \"JWT_SECRET=\$(openssl rand -hex 32)\" >> .env.cloud"
echo ""
