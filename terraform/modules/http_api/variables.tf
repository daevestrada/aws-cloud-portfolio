variable "project_name" {
  description = "Project name — used for resource naming and tagging"
  type        = string
}

variable "environment" {
  description = "Deployment environment (prod, staging)"
  type        = string
  default     = "prod"
}

variable "lambda_zip_path" {
  description = "Path to the Lambda deployment zip file"
  type        = string
}

variable "cors_origin" {
  description = "Allowed origin for the Lambda's own CORS response headers (separate from the API Gateway CORS config below)"
  type        = string
  default     = "https://diegoestrada.cloud"
}

variable "credit_baseline_remaining" {
  description = "AWS credit balance (USD) as of credit_baseline_date — read manually from Billing Console > Credits. Recalibrate whenever a new credit is earned (e.g. an Explore AWS bonus)."
  type        = number
}

variable "credit_baseline_date" {
  description = "Date the credit_baseline_remaining reading was taken (YYYY-MM-DD)"
  type        = string

  validation {
    condition     = can(regex("^\\d{4}-\\d{2}-\\d{2}$", var.credit_baseline_date))
    error_message = "credit_baseline_date must be in YYYY-MM-DD format."
  }
}

variable "credit_expiration_date" {
  description = "Date AWS credits expire (YYYY-MM-DD)"
  type        = string

  validation {
    condition     = can(regex("^\\d{4}-\\d{2}-\\d{2}$", var.credit_expiration_date))
    error_message = "credit_expiration_date must be in YYYY-MM-DD format."
  }
}
