resource "random_password" "db_password" {
  length  = 24
  special = false
}

resource "random_id" "db_suffix" {
  byte_length = 4
}

resource "google_sql_database_instance" "postgres" {
  name             = "${lower(var.project_name)}-${lower(var.environment)}-pg-${random_id.db_suffix.hex}"
  database_version = "POSTGRES_16"
  region           = var.region
  project          = var.project_id

  deletion_protection = var.deletion_protection

  settings {
    tier              = var.tier
    edition           = "ENTERPRISE"
    availability_type = var.availability_type
    activation_policy = var.activation_policy
    disk_type         = "PD_SSD"
    disk_size         = var.disk_size
    disk_autoresize   = true

    ip_configuration {
      ipv4_enabled                                  = false
      private_network                               = var.network_id
      enable_private_path_for_google_cloud_services = true
    }

    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      location                       = var.region
      point_in_time_recovery_enabled = false
      transaction_log_retention_days = 1
    }

    insights_config {
      query_insights_enabled  = false
      query_string_length     = 1024
      record_application_tags = false
    }

    database_flags {
      name  = "max_connections"
      value = "50"
    }
  }

  depends_on = [var.psa_connection]
}

resource "google_sql_database" "database" {
  name     = var.database_name
  instance = google_sql_database_instance.postgres.name
  project  = var.project_id
}

resource "google_sql_user" "user" {
  name     = var.db_user
  instance = google_sql_database_instance.postgres.name
  password = random_password.db_password.result
  project  = var.project_id
}
