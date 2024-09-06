terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Configure the AWS Provider
provider "aws" {
  # no need to specify credentials as long as .env was run
}

# S3 Bucket
resource "aws_s3_bucket" "mlflow-bucket" {
  bucket = var.bucket_name
  tags = {
    Name        = "mlflow-bucket"
    Environment = "Dev"
  }
}