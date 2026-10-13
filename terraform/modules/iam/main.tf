# Backend Cloud Run Service Account
resource "google_service_account" "backend_sa" {
  account_id   = "${lower(var.project_name)}-${lower(var.environment)}-backend-sa"
  display_name = "${var.project_name} ${var.environment} Backend Cloud Run Service Account"
  project      = var.project_id
}

# Frontend Cloud Run Service Account
resource "google_service_account" "frontend_sa" {
  account_id   = "${lower(var.project_name)}-${lower(var.environment)}-frontend-sa"
  display_name = "${var.project_name} ${var.environment} Frontend Cloud Run Service Account"
  project      = var.project_id
}

# GitHub Actions CD Service Account
resource "google_service_account" "github_cd_sa" {
  account_id   = "${lower(var.project_name)}-${lower(var.environment)}-gh-cd"
  display_name = "${var.project_name} ${var.environment} GitHub Actions CD Service Account"
  project      = var.project_id
}

# IAM Role Grants
locals {
  backend_roles = [
    "roles/secretmanager.secretAccessor",
    "roles/aiplatform.user",
    "roles/cloudsql.client",
    "roles/logging.logWriter",
    "roles/storage.objectAdmin",
  ]
  frontend_roles = [
    "roles/secretmanager.secretAccessor",
    "roles/logging.logWriter",
  ]
  cd_roles = [
    "roles/run.admin",
    "roles/artifactregistry.writer",
    "roles/iam.serviceAccountUser",
  ]
}

resource "google_project_iam_member" "backend_role_bindings" {
  for_each = toset(local.backend_roles)
  project  = var.project_id
  role     = each.key
  member   = "serviceAccount:${google_service_account.backend_sa.email}"
}

resource "google_project_iam_member" "frontend_role_bindings" {
  for_each = toset(local.frontend_roles)
  project  = var.project_id
  role     = each.key
  member   = "serviceAccount:${google_service_account.frontend_sa.email}"
}

resource "google_project_iam_member" "cd_role_bindings" {
  for_each = toset(local.cd_roles)
  project  = var.project_id
  role     = each.key
  member   = "serviceAccount:${google_service_account.github_cd_sa.email}"
}

# Workload Identity Pool for GitHub Actions (Passwordless OIDC)
resource "google_iam_workload_identity_pool" "github_pool" {
  count                     = var.enable_workload_identity ? 1 : 0
  workload_identity_pool_id = "${lower(var.project_name)}-${lower(var.environment)}-gh-pool"
  display_name              = "${var.project_name} GitHub Pool"
  project                   = var.project_id
}

resource "google_iam_workload_identity_pool_provider" "github_provider" {
  count                              = var.enable_workload_identity ? 1 : 0
  workload_identity_pool_id          = google_iam_workload_identity_pool.github_pool[0].workload_identity_pool_id
  workload_identity_pool_provider_id = "github-actions-provider"
  display_name                       = "GitHub Actions Provider"
  project                            = var.project_id

  attribute_condition = "assertion.repository == '${var.github_repo}'"

  attribute_mapping = {
    "google.subject"             = "assertion.sub"
    "attribute.actor"            = "assertion.actor"
    "attribute.repository"       = "assertion.repository"
    "attribute.repository_owner" = "assertion.repository_owner"
  }

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

resource "google_service_account_iam_member" "workload_identity_user" {
  count              = var.enable_workload_identity ? 1 : 0
  service_account_id = google_service_account.github_cd_sa.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github_pool[0].name}/attribute.repository/${var.github_repo}"
}
