variable "project_id" {
  description = "GCP Project ID"
  type        = string
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

variable "network_id" {
  description = "VPC network ID for Private IP"
  type        = string
}

variable "psa_connection" {
  description = "Private Service Access peering resource"
  type        = any
}

variable "tier" {
  description = "Cloud SQL machine tier"
  type        = string
  default     = "db-f1-micro"
}

variable "availability_type" {
  description = "ZONAL or REGIONAL (HA)"
  type        = string
  default     = "ZONAL"
}

variable "disk_size" {
  description = "Initial disk size in GB"
  type        = number
  default     = 20
}

variable "shared_buffers" {
  description = "PostgreSQL shared_buffers flag (in 8kB blocks)"
  type        = string
  default     = "65536" # 512MB
}

variable "database_name" {
  description = "Default database name"
  type        = string
  default     = "lak_chemicals"
}

variable "db_user" {
  description = "Database username"
  type        = string
  default     = "lak_app"
}

variable "deletion_protection" {
  description = "Prevent accidental destruction of DB instance"
  type        = bool
  default     = false
}

variable "activation_policy" {
  description = "The activation policy for the instance (ALWAYS, NEVER, ON_DEMAND)"
  type        = string
  default     = "ALWAYS"
}
