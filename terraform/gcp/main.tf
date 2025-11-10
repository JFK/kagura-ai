# Kagura Memory Cloud - GCP Infrastructure
# https://github.com/JFK/kagura-ai/issues/649

terraform {
  required_version = ">= 1.5"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# Compute Engine Instance
resource "google_compute_instance" "kagura" {
  name         = "kagura-memory-cloud"
  machine_type = var.machine_type
  zone         = var.zone

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
      size  = 50  # GB
      type  = "pd-standard"
    }
  }

  network_interface {
    network = "default"

    access_config {
      nat_ip = google_compute_address.kagura_ip.address
    }
  }

  metadata = {
    ssh-keys = "${var.ssh_user}:${file(var.ssh_public_key_path)}"
  }

  metadata_startup_script = file("${path.module}/scripts/install-docker.sh")

  tags = ["kagura", "web", "http-server", "https-server"]

  labels = {
    environment = var.environment
    project     = "kagura-memory-cloud"
  }
}

# Static IP Address
resource "google_compute_address" "kagura_ip" {
  name   = "kagura-static-ip"
  region = var.region
}

# Cloud SQL PostgreSQL Instance
resource "google_sql_database_instance" "postgres" {
  name             = "kagura-postgres-${var.environment}"
  database_version = "POSTGRES_16"
  region           = var.region

  settings {
    tier = var.db_tier

    backup_configuration {
      enabled            = true
      start_time         = "03:00"
      point_in_time_recovery_enabled = true
      transaction_log_retention_days = 7
    }

    ip_configuration {
      ipv4_enabled    = true
      private_network = null

      authorized_networks {
        name  = "kagura-vm"
        value = google_compute_address.kagura_ip.address
      }
    }

    maintenance_window {
      day  = 7  # Sunday
      hour = 3
    }

    database_flags {
      name  = "max_connections"
      value = "100"
    }
  }

  deletion_protection = var.environment == "production" ? true : false
}

# PostgreSQL Database
resource "google_sql_database" "kagura_db" {
  name     = "kagura"
  instance = google_sql_database_instance.postgres.name
}

# PostgreSQL User
resource "google_sql_user" "kagura_user" {
  name     = "kagura_admin"
  instance = google_sql_database_instance.postgres.name
  password = var.db_password
}

# Memorystore Redis Instance
resource "google_redis_instance" "redis" {
  name               = "kagura-redis-${var.environment}"
  tier               = var.redis_tier
  memory_size_gb     = var.redis_memory_gb
  region             = var.region
  redis_version      = "REDIS_7_0"
  display_name       = "Kagura Memory Cloud Redis"

  authorized_network = "default"

  labels = {
    environment = var.environment
    project     = "kagura-memory-cloud"
  }
}

# Cloud Storage Bucket (for backups)
resource "google_storage_bucket" "backups" {
  name          = "${var.project_id}-kagura-backups"
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 90  # days
    }
    action {
      type = "Delete"
    }
  }

  labels = {
    environment = var.environment
    project     = "kagura-memory-cloud"
  }
}

# Firewall Rules
resource "google_compute_firewall" "allow_http" {
  name    = "kagura-allow-http"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["80"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["http-server"]
}

resource "google_compute_firewall" "allow_https" {
  name    = "kagura-allow-https"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["443"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["https-server"]
}

resource "google_compute_firewall" "allow_ssh" {
  name    = "kagura-allow-ssh"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = var.ssh_source_ranges
  target_tags   = ["kagura"]
}
