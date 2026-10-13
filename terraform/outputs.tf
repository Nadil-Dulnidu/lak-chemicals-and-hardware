output "business_server_endpoint" {
  description = "Spring Boot Business Server Cloud Run URI"
  value       = module.cloud_run.business_server_uri
}

output "ai_service_endpoint" {
  description = "FastAPI Multi-Agent AI Service Cloud Run URI"
  value       = module.cloud_run.ai_service_uri
}


output "web_endpoint" {
  description = "Next.js Web Client Cloud Run URI"
  value       = module.cloud_run.web_uri
}

output "product_images_bucket_name" {
  description = "GCS Product Images Bucket Name"
  value       = module.storage.bucket_name
}

output "artifact_registry_docker_url" {
  description = "Artifact Registry Docker URL"
  value       = module.artifact_registry.docker_url
}

output "workload_identity_provider" {
  description = "GitHub Actions Workload Identity Provider"
  value       = module.iam.workload_identity_provider
}

output "github_cd_sa_email" {
  description = "GitHub Actions Service Account Email"
  value       = module.iam.github_cd_sa_email
}

output "database_password" {
  description = "Cloud SQL application user password"
  value       = module.cloud_sql.db_password
  sensitive   = true
}

output "database_url" {
  description = "Cloud SQL database connection string"
  value       = module.cloud_sql.database_url
  sensitive   = true
}
