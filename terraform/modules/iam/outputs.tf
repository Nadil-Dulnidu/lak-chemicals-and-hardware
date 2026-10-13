output "backend_sa_email" {
  description = "Backend Cloud Run Service Account Email"
  value       = google_service_account.backend_sa.email
}

output "frontend_sa_email" {
  description = "Frontend Cloud Run Service Account Email"
  value       = google_service_account.frontend_sa.email
}

output "github_cd_sa_email" {
  description = "GitHub Actions CD Service Account Email"
  value       = google_service_account.github_cd_sa.email
}

output "workload_identity_provider" {
  description = "Full Workload Identity Provider resource name"
  value       = var.enable_workload_identity ? google_iam_workload_identity_pool_provider.github_provider[0].name : ""
}
