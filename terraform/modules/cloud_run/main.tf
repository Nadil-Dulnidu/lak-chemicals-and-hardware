# 1. Spring Boot 3.4 / Java 21 Business Server
resource "google_cloud_run_v2_service" "business_server" {
  name                = "${lower(var.project_name)}-${lower(var.environment)}-business"
  location            = var.region
  project             = var.project_id
  ingress             = "INGRESS_TRAFFIC_ALL"
  deletion_protection = false

  lifecycle {
    ignore_changes = [
      template[0].containers[0].image,
      client,
      client_version,
    ]
  }

  template {
    service_account = var.backend_sa_email

    scaling {
      min_instance_count = var.business_min_instances
      max_instance_count = var.business_max_instances
    }

    vpc_access {
      connector = var.vpc_connector_id
      egress    = "PRIVATE_RANGES_ONLY"
    }

    containers {
      image = var.business_image

      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
        }
      }

      ports {
        container_port = 8000
      }

      env {
        name  = "PORT"
        value = "8000"
      }
      env {
        name  = "SPRING_PROFILES_ACTIVE"
        value = var.environment == "prod" ? "prod" : "dev"
      }
      env {
        name  = "GCS_BUCKET_NAME"
        value = var.product_images_bucket_name
      }
      env {
        name  = "CLERK_JWKS_URL"
        value = var.clerk_jwks_url
      }
      env {
        name  = "CLERK_ISSUER"
        value = var.clerk_issuer
      }

      # Secrets from Secret Manager
      env {
        name = "DATABASE_URL"
        value_source {
          secret_key_ref {
            secret  = var.secret_names["database_url"]
            version = "latest"
          }
        }
      }
      env {
        name = "BUSINESS_SERVER_API_KEY"
        value_source {
          secret_key_ref {
            secret  = var.secret_names["ai_service_api_key"]
            version = "latest"
          }
        }
      }
      env {
        name = "STRIPE_SECRET_KEY"
        value_source {
          secret_key_ref {
            secret  = var.secret_names["stripe_secret_key"]
            version = "latest"
          }
        }
      }
    }
  }
}

# 2. FastAPI + LangGraph AI Service (Multi-Agent Server)
resource "google_cloud_run_v2_service" "ai_service" {
  name                = "${lower(var.project_name)}-${lower(var.environment)}-ai-service"
  location            = var.region
  project             = var.project_id
  ingress             = "INGRESS_TRAFFIC_ALL"
  deletion_protection = false

  lifecycle {
    ignore_changes = [
      template[0].containers[0].image,
      client,
      client_version,
    ]
  }

  template {
    service_account = var.backend_sa_email

    scaling {
      min_instance_count = var.ai_min_instances
      max_instance_count = var.ai_max_instances
    }

    containers {
      image = var.ai_service_image

      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
        }
      }

      ports {
        container_port = 8001
      }

      env {
        name  = "PORT"
        value = "8001"
      }
      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }
      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "GCP_REGION"
        value = var.region
      }
      env {
        name  = "BUSINESS_SERVER_BASE_URL"
        value = google_cloud_run_v2_service.business_server.uri
      }
      env {
        name  = "GEMINI_MODEL"
        value = var.gemini_model
      }
      env {
        name  = "GEMINI_FLASH_MODEL"
        value = var.gemini_flash_model
      }
      env {
        name  = "GEMINI_PRO_MODEL"
        value = var.gemini_pro_model
      }

      # Secrets from Secret Manager
      env {
        name = "AI_SERVICE_API_KEY"
        value_source {
          secret_key_ref {
            secret  = var.secret_names["ai_service_api_key"]
            version = "latest"
          }
        }
      }
      env {
        name = "GENAI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = var.secret_names["genai_api_key"]
            version = "latest"
          }
        }
      }
      env {
        name = "DATABASE_URL"
        value_source {
          secret_key_ref {
            secret  = var.secret_names["database_url"]
            version = "latest"
          }
        }
      }
    }
  }
}

# 3. Next.js Web Client
resource "google_cloud_run_v2_service" "web" {
  name                = "${lower(var.project_name)}-${lower(var.environment)}-web"
  location            = var.region
  project             = var.project_id
  ingress             = "INGRESS_TRAFFIC_ALL"
  deletion_protection = false

  lifecycle {
    ignore_changes = [
      template[0].containers[0].image,
      client,
      client_version,
    ]
  }

  template {
    service_account = var.frontend_sa_email

    scaling {
      min_instance_count = var.web_min_instances
      max_instance_count = var.web_max_instances
    }

    containers {
      image = var.web_image

      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
        }
      }

      ports {
        container_port = 3000
      }

      env {
        name  = "PORT"
        value = "3000"
      }
      env {
        name  = "NEXT_PUBLIC_API_URL"
        value = google_cloud_run_v2_service.business_server.uri
      }
      env {
        name  = "NEXT_PUBLIC_AGENT_API_URL"
        value = google_cloud_run_v2_service.ai_service.uri
      }
      env {
        name  = "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY"
        value = var.clerk_publishable_key
      }
    }
  }
}

# Public Invocation IAM Policy Bindings
resource "google_cloud_run_v2_service_iam_member" "business_server_public" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.business_server.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_v2_service_iam_member" "ai_service_public" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.ai_service.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_v2_service_iam_member" "web_public" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.web.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
