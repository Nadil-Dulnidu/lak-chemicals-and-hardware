resource "google_artifact_registry_repository" "repo" {
  location      = var.region
  repository_id = "${lower(var.project_name)}-${lower(var.environment)}-repo"
  description   = "Docker repository for ${var.project_name} ${var.environment} services"
  format        = "DOCKER"
  project       = var.project_id

  docker_config {
    immutable_tags = false
  }

  cleanup_policies {
    id     = "keep-minimum-versions"
    action = "KEEP"
    most_recent_versions {
      keep_count = 10
    }
  }
}
