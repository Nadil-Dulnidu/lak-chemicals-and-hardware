variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "lak-chem-hrd"
}

variable "project_name" {
  description = "Project name prefix"
  type        = string
  default     = "lak-chemicals"
}

variable "environment" {
  description = "Environment tag (e.g. dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "region" {
  description = "Default GCP Region"
  type        = string
  default     = "asia-south1"
}

variable "github_repo" {
  description = "GitHub repository for Workload Identity Federation"
  type        = string
  default     = "Nadil-Dulnidu/lak-chemicals-and-hardware"
}

variable "clerk_publishable_key" {
  description = "Clerk Frontend Publishable Key"
  type        = string
  default     = ""
}

variable "clerk_secret_key" {
  description = "Clerk Backend Secret Key"
  type        = string
  default     = ""
  sensitive   = true
}

variable "clerk_webhook_signing_secret" {
  description = "Clerk Webhook Signing Secret"
  type        = string
  default     = ""
  sensitive   = true
}

variable "ai_service_api_key" {
  description = "Secret API Key for inter-service communication between backend, AI agent, and API gateway"
  type        = string
  default     = "lak_ai_service_secret_key"
  sensitive   = true
}

variable "stripe_secret_key" {
  description = "Stripe Payment Gateway Secret Key"
  type        = string
  default     = ""
  sensitive   = true
}

variable "genai_api_key" {
  description = "Google Gemini API Key for Express Mode LLM calls"
  type        = string
  default     = ""
  sensitive   = true
}

variable "db_tier" {
  description = "Cloud SQL machine tier (e.g. db-f1-micro for low-cost, db-custom-2-7680 for production)"
  type        = string
  default     = "db-f1-micro"
}

variable "db_activation_policy" {
  description = "Cloud SQL activation policy (ALWAYS to run, NEVER to stop instance and save 100% compute credits)"
  type        = string
  default     = "ALWAYS"
}

variable "deletion_protection" {
  description = "Prevent accidental destruction of DB instance"
  type        = bool
  default     = false
}

variable "business_min_instances" {
  description = "Minimum Business Server instances (0 allows scaling to zero when idle to save cost)"
  type        = number
  default     = 0
}

variable "ai_min_instances" {
  description = "Minimum Multi-Agent AI instances"
  type        = number
  default     = 0
}


variable "web_min_instances" {
  description = "Minimum Web Client instances"
  type        = number
  default     = 0
}

variable "business_image" {
  description = "Docker image for Spring Boot Business Server"
  type        = string
  default     = "us-docker.pkg.dev/cloudrun/container/hello"
}

variable "ai_service_image" {
  description = "Docker image for FastAPI Multi-Agent AI Service"
  type        = string
  default     = "us-docker.pkg.dev/cloudrun/container/hello"
}


variable "web_image" {
  description = "Docker image for Next.js Web Client"
  type        = string
  default     = "us-docker.pkg.dev/cloudrun/container/hello"
}

variable "gemini_model" {
  description = "Primary Gemini LLM model name for AI Service"
  type        = string
  default     = "gemini-2.5-flash"
}

variable "gemini_flash_model" {
  description = "Fast lightweight Gemini model name"
  type        = string
  default     = "gemini-2.5-flash"
}

variable "gemini_pro_model" {
  description = "Deep reasoning Gemini Pro model name"
  type        = string
  default     = "gemini-2.5-pro"
}
