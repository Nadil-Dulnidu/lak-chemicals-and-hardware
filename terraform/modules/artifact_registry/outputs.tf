output "repository_id" {
  description = "Artifact Registry Repository ID"
  value       = google_artifact_registry_repository.repo.repository_id
}

output "repository_name" {
  description = "Artifact Registry Repository Name"
  value       = google_artifact_registry_repository.repo.name
}

output "docker_url" {
  description = "Base Docker registry URL"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.repo.repository_id}"
}
