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

variable "subnet_cidr" {
  description = "Primary subnet IP CIDR"
  type        = string
  default     = "10.0.0.0/20"
}

variable "connector_cidr" {
  description = "Serverless VPC Connector IP CIDR (/28 required)"
  type        = string
  default     = "10.20.0.0/28"
}

variable "connector_min_instances" {
  description = "Minimum Serverless VPC connector instances"
  type        = number
  default     = 2
}

variable "connector_max_instances" {
  description = "Maximum Serverless VPC connector instances"
  type        = number
  default     = 3
}
