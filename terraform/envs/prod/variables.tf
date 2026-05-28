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
