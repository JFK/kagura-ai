# Kagura Memory Cloud - GCP Outputs

output "vm_external_ip" {
  description = "External IP address of the VM"
  value       = google_compute_address.kagura_ip.address
}

output "vm_name" {
  description = "Name of the Compute Engine instance"
  value       = google_compute_instance.kagura.name
}

output "vm_zone" {
  description = "Zone of the Compute Engine instance"
  value       = google_compute_instance.kagura.zone
}

output "postgres_connection_name" {
  description = "Cloud SQL connection name"
  value       = google_sql_database_instance.postgres.connection_name
}

output "postgres_public_ip" {
  description = "Cloud SQL public IP address"
  value       = google_sql_database_instance.postgres.public_ip_address
}

output "postgres_database" {
  description = "PostgreSQL database name"
  value       = google_sql_database.kagura_db.name
}

output "postgres_user" {
  description = "PostgreSQL admin username"
  value       = google_sql_user.kagura_user.name
  sensitive   = true
}

output "redis_host" {
  description = "Redis host address"
  value       = google_redis_instance.redis.host
}

output "redis_port" {
  description = "Redis port"
  value       = google_redis_instance.redis.port
}

output "storage_bucket_name" {
  description = "Cloud Storage bucket name for backups"
  value       = google_storage_bucket.backups.name
}

output "storage_bucket_url" {
  description = "Cloud Storage bucket URL"
  value       = google_storage_bucket.backups.url
}

# Connection strings for convenience
output "database_url" {
  description = "PostgreSQL connection URL (for .env)"
  value       = "postgresql://${google_sql_user.kagura_user.name}:${var.db_password}@${google_sql_database_instance.postgres.public_ip_address}:5432/${google_sql_database.kagura_db.name}"
  sensitive   = true
}

output "redis_url" {
  description = "Redis connection URL (for .env)"
  value       = "redis://${google_redis_instance.redis.host}:${google_redis_instance.redis.port}"
  sensitive   = true
}

output "ssh_command" {
  description = "SSH command to connect to the VM"
  value       = "gcloud compute ssh ${google_compute_instance.kagura.name} --zone=${google_compute_instance.kagura.zone}"
}
