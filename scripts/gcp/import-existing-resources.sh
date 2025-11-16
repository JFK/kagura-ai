#!/bin/bash
# Import existing GCP resources into Terraform state

set -e

cd "$(dirname "$0")"

PROJECT_ID="kagura-memory-cloud"
REGION="asia-northeast1"
ZONE="asia-northeast1-a"

echo "🔄 Importing existing GCP resources into Terraform state..."
echo ""

# Import Compute Address
echo "📍 Importing Static IP..."
terraform import google_compute_address.kagura_ip \
  "projects/${PROJECT_ID}/regions/${REGION}/addresses/kagura-static-ip" || echo "  ⚠️  Already imported or not found"

# Import Firewall Rules
echo "🔥 Importing Firewall Rules..."
terraform import google_compute_firewall.allow_ssh \
  "projects/${PROJECT_ID}/global/firewalls/kagura-allow-ssh" || echo "  ⚠️  Already imported or not found"

terraform import google_compute_firewall.allow_http \
  "projects/${PROJECT_ID}/global/firewalls/kagura-allow-http" || echo "  ⚠️  Already imported or not found"

terraform import google_compute_firewall.allow_https \
  "projects/${PROJECT_ID}/global/firewalls/kagura-allow-https" || echo "  ⚠️  Already imported or not found"

# Import Redis Instance
echo "🔴 Importing Redis Instance..."
terraform import google_redis_instance.redis \
  "projects/${PROJECT_ID}/locations/${REGION}/instances/kagura-redis-production" || echo "  ⚠️  Already imported or not found"

# Import Storage Bucket
echo "🗄️  Importing Storage Bucket..."
terraform import google_storage_bucket.backups \
  "kagura-memory-cloud-kagura-backups" || echo "  ⚠️  Already imported or not found"

# Import Compute Instance (if exists)
echo "💻 Importing Compute Instance..."
terraform import google_compute_instance.kagura \
  "projects/${PROJECT_ID}/zones/${ZONE}/instances/kagura-memory-cloud" || echo "  ⚠️  Not found (will be created)"

# Import SQL Database Instance (if exists)
echo "🗄️  Importing PostgreSQL Instance..."
terraform import google_sql_database_instance.postgres \
  "kagura-postgres-production" || echo "  ⚠️  Not found (will be created)"

# Import SQL Database (if exists)
echo "🗄️  Importing Database..."
terraform import google_sql_database.kagura_db \
  "projects/${PROJECT_ID}/instances/kagura-postgres-production/databases/kagura" || echo "  ⚠️  Not found (will be created)"

# Import SQL User (if exists)
echo "👤 Importing Database User..."
terraform import google_sql_user.kagura_user \
  "kagura-postgres-production/kagura_admin" || echo "  ⚠️  Not found (will be created)"

echo ""
echo "✅ Import completed!"
echo ""
echo "Next steps:"
echo "  1. Run: terraform plan"
echo "  2. Review changes"
echo "  3. Run: terraform apply"
