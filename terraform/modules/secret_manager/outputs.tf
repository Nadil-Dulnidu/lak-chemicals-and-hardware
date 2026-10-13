output "secret_ids" {
  description = "Map of created secret IDs"
  value       = { for k, v in google_secret_manager_secret.secret : k => v.secret_id }
}

output "secret_names" {
  description = "Map of created secret resource names"
  value       = { for k, v in google_secret_manager_secret.secret : k => v.name }
}
