module "static_site" {
  source = "../../modules/static_site"

  project_name        = var.project_name
  environment         = var.environment
  domain_name         = var.domain_name
  acm_certificate_arn = var.acm_certificate_arn
}

module "http_api" {
  source = "../../modules/http_api"

  project_name    = var.project_name
  environment     = var.environment
  lambda_zip_path = var.lambda_zip_path
}
