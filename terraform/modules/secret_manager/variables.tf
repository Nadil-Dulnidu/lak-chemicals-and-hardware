variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "lak-chem-hrd"
}

variable "project_name" {
  description = "Application project prefix"
  type        = string
  default     = "lak-chemicals"
}

variable "environment" {
  description = "Deployment environment (staging/production)"
  type        = string
  default     = "prod"
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
  description = "Secret API key for inter-service communication (backend, AI agent, gateway)"
  type        = string
  default     = ""
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

variable "database_url" {
  description = "PostgreSQL Database Connection String"
  type        = string
  default     = ""
  sensitive   = true
}
