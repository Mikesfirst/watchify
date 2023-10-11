terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region     = "us-east-1"
  access_key = "AKIA3ZGLXBQVC3JU3V73"
  secret_key = "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"
}