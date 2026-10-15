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

variable "region" {
  description = "GCP region"
  type        = string
  default     = "asia-south1"
}

variable "backend_sa_email" {
  description = "Backend Service Account Email"
  type        = string
}

variable "frontend_sa_email" {
  description = "Frontend Service Account Email"
  type        = string
}

variable "vpc_connector_id" {
  description = "Serverless VPC Access Connector ID"
  type        = string
}

variable "business_image" {
  description = "Docker image URI for Spring Boot Business Server"
  type        = string
  default     = "us-docker.pkg.dev/cloudrun/container/hello"
}

variable "ai_service_image" {
  description = "Docker image URI for FastAPI Multi-Agent AI Service"
  type        = string
  default     = "us-docker.pkg.dev/cloudrun/container/hello"
}


variable "web_image" {
  description = "Docker image URI for Next.js Web Client"
  type        = string
  default     = "us-docker.pkg.dev/cloudrun/container/hello"
}

variable "product_images_bucket_name" {
  description = "GCS bucket name for product images"
  type        = string
}

variable "clerk_issuer" {
  description = "Clerk JWT Issuer authority"
  type        = string
  default     = "https://delicate-civet-49.clerk.accounts.dev"
}

variable "clerk_jwks_url" {
  description = "Clerk JWKS URL"
  type        = string
  default     = "https://delicate-civet-49.clerk.accounts.dev/.well-known/jwks.json"
}

variable "clerk_publishable_key" {
  description = "Clerk Frontend Publishable Key"
  type        = string
  default     = ""
}

variable "secret_names" {
  description = "Map of Secret Manager secret names"
  type        = map(string)
}

variable "business_min_instances" {
  description = "Min Business Server instances (0 allows scaling to zero to save costs)"
  type        = number
  default     = 0
}

variable "business_max_instances" {
  description = "Max Business Server instances"
  type        = number
  default     = 3
}

variable "ai_min_instances" {
  description = "Min AI Service instances"
  type        = number
  default     = 0
}

variable "ai_max_instances" {
  description = "Max AI Service instances"
  type        = number
  default     = 2
}


variable "web_min_instances" {
  description = "Min Web Client instances"
  type        = number
  default     = 0
}

variable "web_max_instances" {
  description = "Max Web Client instances"
  type        = number
  default     = 2
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
