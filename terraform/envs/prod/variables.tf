variable "project_name" {
  description = "Project name"
  type        = string
  default     = "aws-cloud-portfolio"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "prod"
}

variable "domain_name" {
  description = "Primary domain name"
  type        = string
}

variable "acm_certificate_arn" {
  description = "ACM certificate ARN in us-east-1"
  type        = string
}

variable "lambda_zip_path" {
  description = "Path to the Lambda deployment zip file"
  type        = string
  default     = "../../src/lambda/cost/cost.zip"
}

variable "credit_baseline_remaining" {
  description = "AWS credit balance (USD) as of credit_baseline_date — read manually from Billing Console > Credits. Recalibrate whenever a new credit is earned."
  type        = number
}

variable "credit_baseline_date" {
  description = "Date the credit_baseline_remaining reading was taken (YYYY-MM-DD)"
  type        = string
}

variable "credit_expiration_date" {
  description = "Date AWS credits expire (YYYY-MM-DD)"
  type        = string
}
