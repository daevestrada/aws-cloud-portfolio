variable "project_name" {
  description = "Project name — used for resource naming and tagging"
  type        = string
}

variable "environment" {
  description = "Deployment environment (prod, staging)"
  type        = string
  default     = "prod"
}

variable "domain_name" {
  description = "Primary domain name for the CloudFront distribution (e.g. example.com)"
  type        = string
}

variable "acm_certificate_arn" {
  description = "ARN of the ACM certificate in us-east-1 for the domain"
  type        = string
}
