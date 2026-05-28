terraform {
  required_version = ">= 1.9"

  backend "s3" {
    bucket         = "tfstate-309615787255"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "tfstate-locks"  # use_lockfile is still experimental — keeping dynamodb_table
    encrypt        = true
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"

  default_tags {
    tags = {
      Project = "aws-cloud-portfolio"
      Owner   = "diego-estrada"
    }
  }
}
