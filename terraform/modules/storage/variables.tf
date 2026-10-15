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
  description = "Deployment environment"
  type        = string
  default     = "prod"
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "asia-south1"
}

variable "backend_sa_email" {
  description = "Service account email of backend API to grant storage access"
  type        = string
}
