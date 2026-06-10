output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  value       = module.static_site.cloudfront_domain_name
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = module.static_site.cloudfront_distribution_id
}

output "s3_bucket_name" {
  description = "S3 bucket name"
  value       = module.static_site.s3_bucket_name
}

output "api_endpoint" {
  description = "API Gateway endpoint URL"
  value       = module.http_api.api_endpoint
}

output "lambda_function_name" {
  description = "Lambda function name"
  value       = module.http_api.lambda_function_name
}
