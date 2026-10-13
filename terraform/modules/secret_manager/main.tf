locals {
  secrets = {
    "clerk_secret_key"             = var.clerk_secret_key
    "clerk_webhook_signing_secret" = var.clerk_webhook_signing_secret
    "ai_service_api_key"           = var.ai_service_api_key
    "stripe_secret_key"            = var.stripe_secret_key
    "genai_api_key"                = var.genai_api_key
    "database_url"                 = var.database_url
  }

  secret_keys = toset([
    "clerk_secret_key",
    "clerk_webhook_signing_secret",
    "ai_service_api_key",
    "stripe_secret_key",
    "genai_api_key",
    "database_url",
  ])
}

resource "google_secret_manager_secret" "secret" {
  for_each  = local.secret_keys
  secret_id = "${lower(var.project_name)}-${lower(var.environment)}-${replace(each.key, "_", "-")}"
  project   = var.project_id

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "secret_version" {
  for_each    = local.secret_keys
  secret      = google_secret_manager_secret.secret[each.key].id
  secret_data = local.secrets[each.key] != null && length(trimspace(local.secrets[each.key])) > 0 ? local.secrets[each.key] : "placeholder_not_set"
}
