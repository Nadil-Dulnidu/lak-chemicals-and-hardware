output "instance_name" {
  description = "Cloud SQL instance name"
  value       = google_sql_database_instance.postgres.name
}

output "instance_connection_name" {
  description = "Cloud SQL instance connection name (project:region:instance)"
  value       = google_sql_database_instance.postgres.connection_name
}

output "private_ip_address" {
  description = "Private IP address of the PostgreSQL instance"
  value       = google_sql_database_instance.postgres.private_ip_address
}

output "database_name" {
  description = "Application database name"
  value       = google_sql_database.database.name
}

output "db_user" {
  description = "Application database username"
  value       = google_sql_user.user.name
}

output "db_password" {
  description = "Generated application database password"
  value       = random_password.db_password.result
  sensitive   = true
}

output "database_url" {
  description = "Standard PostgreSQL connection string"
  value       = "postgresql://${google_sql_user.user.name}:${random_password.db_password.result}@${google_sql_database_instance.postgres.private_ip_address}:5432/${google_sql_database.database.name}"
  sensitive   = true
}
